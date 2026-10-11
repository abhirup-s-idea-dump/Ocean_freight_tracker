"""
Email-based Rate and Shipment Update Parser (Module 4)
Parses plain-text shipping emails, extracts structured data for:
1. Rate revisions (Carrier, Origin, Destination, Container, Rate, Effective Date)
2. Shipment status alerts (Shipment ID, Status: In Transit / Delivered / Delayed, Notes, Delivery Date)
3. Filters out marketing newsletters, out-of-office notes, and malformed emails gracefully.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

CARRIER_DOMAINS = {
    'oceanlinklines.com': 'OceanLink Lines',
    'bluewaveshipping.com': 'BlueWave Shipping',
    'globalmariner.com': 'GlobalMariner',
    'pacificstarline.com': 'PacificStar Line',
    'atlasseacarriers.com': 'AtlasSea Carriers',
}

KNOWN_CARRIERS = [
    'OceanLink Lines',
    'BlueWave Shipping',
    'GlobalMariner',
    'PacificStar Line',
    'AtlasSea Carriers',
]

KNOWN_PORTS = [
    'Nhava Sheva',
    'Mundra',
    'Chennai',
    'Kolkata',
    'Los Angeles',
    'New York',
    'Savannah',
    'Houston',
    'Long Beach',
    'Norfolk',
]


def extract_headers_and_body(raw_text: str) -> Dict[str, Any]:
    """Extract standard email headers (From, Subject, Date) and message body."""
    lines = raw_text.strip().splitlines()
    headers = {'From': '', 'Subject': '', 'Date': ''}
    body_lines = []
    in_body = False

    for line in lines:
        stripped = line.strip()
        if not in_body:
            if stripped.startswith('From:'):
                headers['From'] = stripped.split(':', 1)[1].strip()
            elif stripped.startswith('Subject:'):
                headers['Subject'] = stripped.split(':', 1)[1].strip()
            elif stripped.startswith('Date:'):
                headers['Date'] = stripped.split(':', 1)[1].strip()
            elif stripped == '' and (headers['From'] or headers['Subject']):
                in_body = True
        else:
            body_lines.append(line)

    body = '\n'.join(body_lines).strip()
    # If no headers were detected, consider the whole text as body
    if not headers['From'] and not headers['Subject'] and not in_body:
        body = raw_text.strip()

    return {
        'headers': headers,
        'body': body
    }


def identify_carrier(sender: str, text: str) -> Optional[str]:
    """Identify carrier from email address domain or text mentions."""
    # Check domain
    sender_lower = sender.lower()
    for domain, carrier in CARRIER_DOMAINS.items():
        if domain in sender_lower:
            return carrier

    # Check known carrier names in text
    text_lower = text.lower()
    for carrier in KNOWN_CARRIERS:
        if carrier.lower() in text_lower:
            return carrier

    # Fuzzy matches
    if 'oceanlink' in text_lower or 'ocean link' in text_lower:
        return 'OceanLink Lines'
    if 'bluewave' in text_lower or 'blue wave' in text_lower:
        return 'BlueWave Shipping'
    if 'globalmariner' in text_lower or 'global mariner' in text_lower:
        return 'GlobalMariner'
    if 'pacificstar' in text_lower or 'pacific star' in text_lower:
        return 'PacificStar Line'
    if 'atlassea' in text_lower or 'atlas sea' in text_lower:
        return 'AtlasSea Carriers'

    return None


def parse_date(date_str: str) -> Optional[str]:
    """Parse dates in various formats into YYYY-MM-DD."""
    if not date_str:
        return None
    date_str = date_str.strip()
    # Format: YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    # Format: 11 Aug 2026, 25 Sep 2026
    m = re.search(r'(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})', date_str)
    if m:
        day, month_str, year = m.groups()
        month_abbr = month_str[:3].capitalize()
        try:
            dt = datetime.strptime(f"{day} {month_abbr} {year}", "%d %b %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_email(raw_text: str, email_index: int = 1) -> Dict[str, Any]:
    """
    Parse an email text to extract updates or identify irrelevant messages.
    Returns structured dict with type, status, extracted data, and explanation.
    """
    extracted = extract_headers_and_body(raw_text)
    headers = extracted['headers']
    body = extracted['body']
    sender = headers.get('From', '')
    subject = headers.get('Subject', '')
    email_date = headers.get('Date', '')
    full_text = f"{subject}\n{body}"

    carrier = identify_carrier(sender, full_text)

    # 1. Filter out spam / newsletters
    if any(k in sender.lower() for k in ['newsletter', 'news@', 'marketing@']) or \
       any(k in subject.lower() for k in ['newsletter', 'shipping news', 'weekly digest']) or \
       'unsubscribe' in body.lower():
        return {
            'email_index': email_index,
            'type': 'ignored',
            'action': 'skip',
            'reason': 'Marketing or newsletter email (non-operational)',
            'headers': headers,
            'body': body,
            'extracted_data': {}
        }

    # 2. Filter out out-of-office notices
    if 'out of office' in subject.lower() or 'out of office' in body.lower() or 'away from office' in body.lower():
        return {
            'email_index': email_index,
            'type': 'ignored',
            'action': 'skip',
            'reason': 'Out of Office automated notification',
            'headers': headers,
            'body': body,
            'extracted_data': {}
        }

    # 3. Check for Shipment Updates
    shp_match = re.search(r'\b(SHP\d{4})\b', full_text, re.IGNORECASE)
    is_shipment_context = any(k in full_text.lower() for k in ['shipment', 'tracking', 'delivered', 'delayed', 'in transit', 'delivery confirmation']) or \
                          any(k in sender.lower() for k in ['tracking@', 'ops@'])

    if is_shipment_context:
        if not shp_match:
            return {
                'email_index': email_index,
                'type': 'ignored',
                'action': 'skip',
                'reason': 'Malformed shipment alert: No shipment ID (e.g. SHP####) found',
                'headers': headers,
                'body': body,
                'extracted_data': {}
            }

        shipment_id = shp_match.group(1).upper()
        status = 'In Transit'
        delivered_date = None
        notes = []

        # Determine status
        if re.search(r'\bdelivered\b', full_text, re.IGNORECASE):
            status = 'Delivered'
            # Look for delivery date in text: e.g. "on 11 Aug 2026"
            date_m = re.search(r'(?:on|at|delivered)\s+(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})', full_text, re.IGNORECASE)
            if date_m:
                delivered_date = parse_date(date_m.group(1))
            if not delivered_date:
                delivered_date = parse_date(email_date)
            notes.append("Delivered successfully")
        elif re.search(r'\bdelayed\b', full_text, re.IGNORECASE):
            status = 'Delayed'
            # Look for delay reasons: port congestion, vessel rescheduling, weather
            reason_m = re.search(r'due to ([^\.\n]+)', full_text, re.IGNORECASE)
            if reason_m:
                notes.append(f"Reason: {reason_m.group(1).strip()}")
            delay_days_m = re.search(r'delayed by\s+(?:approximately\s+)?(\d+\s+days?)', full_text, re.IGNORECASE)
            if delay_days_m:
                notes.append(f"Duration: {delay_days_m.group(1).strip()}")
        elif re.search(r'\bin transit\b', full_text, re.IGNORECASE):
            status = 'In Transit'
            notes.append("Vessel in transit; no delays reported")

        return {
            'email_index': email_index,
            'type': 'shipment_update',
            'action': 'update_shipment',
            'reason': f"Extracted status '{status}' for {shipment_id}",
            'headers': headers,
            'body': body,
            'extracted_data': {
                'shipment_id': shipment_id,
                'status': status,
                'delivered_date': delivered_date,
                'carrier': carrier,
                'notes': ' | '.join(notes) if notes else None,
                'email_date': email_date
            }
        }

    # 4. Check for Rate Updates
    is_rate_context = any(k in full_text.lower() for k in ['rate', 'tariff', 'pricing', 'revised', 'usd', '$']) or \
                      any(k in sender.lower() for k in ['pricing@', 'rates@'])

    if is_rate_context:
        # Check if email explicitly mentions missing attachment or lack of details
        if 'attached sheet' in full_text.lower() or 'check attachment' in full_text.lower() or 'attachment not included' in full_text.lower():
            # If no price is in the text, it cannot be parsed
            if not re.search(r'(?:USD|\$)\s*[\d,]+', full_text, re.IGNORECASE):
                return {
                    'email_index': email_index,
                    'type': 'ignored',
                    'action': 'skip',
                    'reason': 'Incomplete rate update: Rate details referenced in external attachment',
                    'headers': headers,
                    'body': body,
                    'extracted_data': {}
                }

        # Container type
        container_type = None
        if '20ft' in full_text.lower() or '20 ft' in full_text.lower() or "20'" in full_text:
            container_type = '20ft'
        elif '40ft' in full_text.lower() or '40 ft' in full_text.lower() or "40'" in full_text:
            container_type = '40ft'

        # Rate USD
        rate_usd = None
        rate_m = re.search(r'(?:USD|\$)\s*([\d,]+(?:\.\d{1,2})?)', full_text, re.IGNORECASE)
        if rate_m:
            try:
                rate_usd = float(rate_m.group(1).replace(',', ''))
            except ValueError:
                pass

        # Effective date
        effective_date = None
        eff_m = re.search(r'(?:effective|valid)\s+(?:from\s+)?(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})', full_text, re.IGNORECASE)
        if eff_m:
            effective_date = parse_date(eff_m.group(1))
        elif 'immediately' in full_text.lower():
            effective_date = parse_date(email_date) or datetime.today().strftime('%Y-%m-%d')

        # Detect Origin and Destination Ports
        found_ports = []
        for port in KNOWN_PORTS:
            pattern = rf'\b{re.escape(port)}\b'
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                found_ports.append((match.start(), port))

        # Sort by appearance index
        found_ports.sort(key=lambda x: x[0])
        # Deduplicate sequential identical mentions
        unique_ports = []
        for _, p in found_ports:
            if not unique_ports or unique_ports[-1] != p:
                unique_ports.append(p)

        origin_port = None
        destination_port = None
        if len(unique_ports) >= 2:
            origin_port = unique_ports[0]
            destination_port = unique_ports[1]
        elif len(unique_ports) == 1:
            origin_port = unique_ports[0]

        # Validation
        if not carrier or not origin_port or not destination_port or not container_type or not rate_usd:
            missing_fields = []
            if not carrier: missing_fields.append("Carrier")
            if not origin_port: missing_fields.append("Origin Port")
            if not destination_port: missing_fields.append("Destination Port")
            if not container_type: missing_fields.append("Container Type")
            if not rate_usd: missing_fields.append("Rate (USD)")
            return {
                'email_index': email_index,
                'type': 'ignored',
                'action': 'skip',
                'reason': f"Incomplete rate email: Missing required fields ({', '.join(missing_fields)})",
                'headers': headers,
                'body': body,
                'extracted_data': {
                    'carrier': carrier,
                    'origin_port': origin_port,
                    'destination_port': destination_port,
                    'container_type': container_type,
                    'rate_usd': rate_usd
                }
            }

        return {
            'email_index': email_index,
            'type': 'rate_update',
            'action': 'update_rate',
            'reason': f"New {container_type} rate USD ${rate_usd:,.2f} for {carrier} ({origin_port} -> {destination_port})",
            'headers': headers,
            'body': body,
            'extracted_data': {
                'carrier': carrier,
                'origin_port': origin_port,
                'destination_port': destination_port,
                'container_type': container_type,
                'rate_usd': rate_usd,
                'effective_date': effective_date
            }
        }

    return {
        'email_index': email_index,
        'type': 'ignored',
        'action': 'skip',
        'reason': 'Unrecognized content / general inquiry',
        'headers': headers,
        'body': body,
        'extracted_data': {}
    }


def parse_email_inbox(file_path: str) -> List[Dict[str, Any]]:
    """Parse all emails in the sample inbox text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by "Email X" or delimiter lines
    email_blocks = re.split(r'Email\s+(\d+)', content)
    results = []

    # First block is preamble if it doesn't have Email 1
    if len(email_blocks) > 1:
        for i in range(1, len(email_blocks), 2):
            idx = int(email_blocks[i])
            body_block = email_blocks[i + 1].strip()
            # remove trailing separator dashes
            body_block = re.sub(r'-{10,}$', '', body_block).strip()
            parsed = parse_email(body_block, email_index=idx)
            results.append(parsed)
    else:
        # Fallback to dashed line split
        parts = content.split('----------------------------------------------------------------------')
        idx = 1
        for part in parts:
            cleaned = part.strip()
            if cleaned and 'From:' in cleaned:
                parsed = parse_email(cleaned, email_index=idx)
                results.append(parsed)
                idx += 1

    return results


if __name__ == '__main__':
    import os
    sample_file = os.path.join(os.path.dirname(__file__), 'data', 'sample_emails.txt')
    if os.path.exists(sample_file):
        items = parse_email_inbox(sample_file)
        print(f"Parsed {len(items)} emails:")
        for item in items:
            print(f"[{item['email_index']:02d}] Type: {item['type']:<16} Action: {item['action']:<15} Detail: {item['reason']}")
