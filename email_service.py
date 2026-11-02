import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EmailService')

# In-memory log of sent/attempted emails for admin audit
EMAIL_ACTIVITY_LOGS = []

def send_email(subject, recipients, html_content, config, cc=None, attachments=None):
    """
    Sends an email using the SMTP settings provided in config.
    Supports HTML content, multiple recipients, CC, and multiple file/image attachments.
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if not isinstance(recipients, list):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]
        
    cc_list = []
    if cc:
        if isinstance(cc, list):
            cc_list = [c.strip() for c in cc if c.strip()]
        else:
            cc_list = [c.strip() for c in cc.split(',') if c.strip()]

    sender = config.get('MAIL_DEFAULT_SENDER') or 'divya.trading06@gmail.com'
    mail_server = config.get('MAIL_SERVER') or 'smtp.gmail.com'
    try:
        mail_port = int(config.get('MAIL_PORT') or 587)
    except (ValueError, TypeError):
        mail_port = 587
        
    username = (config.get('MAIL_USERNAME') or '').strip()
    password = (config.get('MAIL_PASSWORD') or '').strip().replace(' ', '')
    use_tls = config.get('MAIL_USE_TLS', True)
    use_ssl = config.get('MAIL_USE_SSL', False) or (mail_port == 465)
    
    all_recipients = list(dict.fromkeys(recipients + cc_list))

    log_entry = {
        'timestamp': timestamp,
        'subject': subject,
        'recipients': all_recipients,
        'sender': sender,
        'status': 'pending',
        'attachments_count': len(attachments) if attachments else 0,
        'error': None
    }
    
    # Check if SMTP credentials are provided
    if not username or not password:
        log_entry['status'] = 'simulated'
        log_entry['note'] = 'SMTP credentials not configured. Please enter your SMTP username & App Password in Website CMS & Settings.'
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        logger.info(f"[SIMULATED EMAIL] To: {all_recipients} | Subject: {subject} | Attachments: {len(attachments) if attachments else 0}")
        return True, "Email recorded (Simulated - configure SMTP in settings for inbox delivery)"
        
    try:
        if attachments:
            msg = MIMEMultipart('mixed')
            alt_part = MIMEMultipart('alternative')
            alt_part.attach(MIMEText(html_content, 'html'))
            msg.attach(alt_part)
            
            for att in attachments:
                if isinstance(att, dict):
                    fname = att.get('filename')
                    fdata = att.get('content')
                    ctype = att.get('content_type')
                else:
                    fname, fdata, ctype = att
                    
                if not fname or not fdata:
                    continue
                    
                maintype, subtype = (ctype.split('/', 1) if ctype and '/' in ctype else ('application', 'octet-stream'))
                part = MIMEBase(maintype, subtype)
                part.set_payload(fdata)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{fname}"')
                msg.attach(part)
        else:
            msg = MIMEMultipart('alternative')
            part = MIMEText(html_content, 'html')
            msg.attach(part)

        msg['Subject'] = subject
        msg['From'] = f"Divya Trading Co. <{sender}>"
        msg['To'] = ", ".join(recipients)
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        
        if use_ssl or mail_port == 465:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=15)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=15)
            if use_tls:
                server.starttls()
                
        server.login(username, password)
        server.sendmail(sender, all_recipients, msg.as_string())
        server.quit()
        
        log_entry['status'] = 'sent'
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        logger.info(f"[EMAIL SENT] To: {all_recipients} | Subject: {subject}")
        return True, "Email sent successfully"
    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"SMTP Authentication Failed: Mail server rejected username or password. If using Gmail, please use a 16-character App Password (not your normal password)."
        logger.error(f"[EMAIL AUTH ERROR] {err_msg}")
        log_entry['status'] = 'failed'
        log_entry['error'] = err_msg
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        return False, err_msg
    except smtplib.SMTPConnectError as e:
        err_msg = f"Could not connect to SMTP server ({mail_server}:{mail_port}). Please verify port and server address."
        logger.error(f"[EMAIL CONNECT ERROR] {err_msg}")
        log_entry['status'] = 'failed'
        log_entry['error'] = err_msg
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        return False, err_msg
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed sending to {all_recipients}: {str(e)}")
        log_entry['status'] = 'failed'
        log_entry['error'] = str(e)
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        return False, str(e)


def notify_admin_new_inquiry(inquiry, config):
    """
    Sends email notification to the DTC admin team when a new inquiry arrives.
    """
    admin_emails = config.get('ADMIN_NOTIFICATION_EMAIL', 'divya.trading06@gmail.com,neelbarot585@gmail.com')
    subject = f"[New Inquiry #{inquiry.inquiry_number}] from {inquiry.customer_name} ({inquiry.company_name or 'Individual'})"
    
    items_html = ""
    for idx, item in enumerate(inquiry.items, 1):
        items_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; font-weight: 600; color: #0A2540;">#{idx}</td>
            <td style="padding: 10px; color: #1e293b;">
                <strong>{item.product_name}</strong>
                {f'<br><span style="color:#64748b; font-size:12px;">Part No: {item.part_number}</span>' if item.part_number else ''}
            </td>
            <td style="padding: 10px; text-align: center; color: #0052CC; font-weight: 700;">{item.quantity}</td>
            <td style="padding: 10px; color: #64748b; font-size: 13px;">{item.notes or 'N/A'}</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #0A2540; padding: 24px; text-align: center; border-bottom: 4px solid #0052CC;">
                <h2 style="color: #ffffff; margin: 0; font-size: 22px; letter-spacing: 0.5px;">DIVYA TRADING CO.</h2>
                <p style="color: #93c5fd; margin: 4px 0 0; font-size: 13px;">Rotary Printing Machine Spares - Inquiry Alert</p>
            </div>
            <div style="padding: 24px;">
                <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px; margin-bottom: 20px;">
                    <div>
                        <span style="font-size: 12px; color: #64748b; text-transform: uppercase;">Inquiry Reference</span>
                        <h3 style="margin: 2px 0 0; color: #0052CC; font-size: 18px;">#{inquiry.inquiry_number}</h3>
                    </div>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #f8fafc; border-radius: 8px; overflow: hidden;">
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px; width: 35%;">Customer Name:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-weight: 600; font-size: 14px;">{inquiry.customer_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Company Name:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-weight: 600; font-size: 14px;">{inquiry.company_name or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Email Address:</td>
                        <td style="padding: 10px 14px; color: #0052CC; font-size: 14px;"><a href="mailto:{inquiry.email}">{inquiry.email}</a></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Phone / WhatsApp:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-weight: 600; font-size: 14px;">
                            <a href="https://wa.me/{inquiry.phone.replace('+', '').replace(' ', '')}" style="color: #16a34a; text-decoration: none;">{inquiry.phone} (WhatsApp)</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Country / Location:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-size: 14px;">{inquiry.country or 'India'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Machine Model:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-weight: 600; font-size: 14px;">{inquiry.machine_model or 'Not Specified'}</td>
                    </tr>
                </table>

                <h4 style="color: #0A2540; margin: 20px 0 10px; font-size: 16px;">Requested Products / Parts:</h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                    <thead>
                        <tr style="background: #e2e8f0; text-align: left;">
                            <th style="padding: 10px; color: #475569; font-size: 12px;">#</th>
                            <th style="padding: 10px; color: #475569; font-size: 12px;">Product Details</th>
                            <th style="padding: 10px; color: #475569; font-size: 12px; text-align: center;">Qty</th>
                            <th style="padding: 10px; color: #475569; font-size: 12px;">Requirements</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                {f'''
                <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px; border-radius: 4px; margin-bottom: 20px;">
                    <strong style="color: #92400e; font-size: 13px;">Customer Message / Special Requirements:</strong>
                    <p style="color: #78350f; margin: 6px 0 0; font-size: 14px; line-height: 1.5;">{inquiry.message}</p>
                </div>
                ''' if inquiry.message else ''}

                <div style="text-align: center; margin-top: 25px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                    <a href="http://127.0.0.1:5000/admin" style="background: #0052CC; color: #ffffff; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px; display: inline-block;">Open Admin Panel</a>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 14px; text-align: center; font-size: 12px; color: #64748b;">
                DIVYA TRADING CO. • Ahmedabad, Gujarat, India • Automated Inquiry Dispatch
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(subject, admin_emails, html, config)


def send_customer_acknowledgment(inquiry, config):
    """
    Sends an acknowledgment email to the customer with DTC contact details.
    """
    if not inquiry.email:
        return False, "No customer email provided"
        
    subject = f"Thank you for your inquiry with Divya Trading Co. [Ref: #{inquiry.inquiry_number}]"
    
    items_html = ""
    for idx, item in enumerate(inquiry.items, 1):
        items_html += f"""
        <li style="margin-bottom: 8px; color: #334155;">
            <strong>{item.product_name}</strong> {f'({item.part_number})' if item.part_number else ''} — <strong>Qty: {item.quantity}</strong>
            {f'<span style="color:#64748b; font-size:12px;"> ({item.notes})</span>' if item.notes else ''}
        </li>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #0A2540; padding: 24px; text-align: center;">
                <h2 style="color: #ffffff; margin: 0; font-size: 22px;">DIVYA TRADING CO.</h2>
                <p style="color: #93c5fd; margin: 4px 0 0; font-size: 13px;">Manufacturer & Exporter of Textile Printing Machine Spares</p>
            </div>
            <div style="padding: 24px;">
                <p style="font-size: 15px; color: #1e293b;">Dear <strong>{inquiry.customer_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569; line-height: 1.6;">
                    Thank you for contacting Divya Trading Co. We have received your inquiry <strong>#{inquiry.inquiry_number}</strong>. Our technical and sales team will review your specifications and get back to you promptly with pricing and lead times.
                </p>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0;">
                    <h4 style="margin: 0 0 10px; color: #0A2540; font-size: 14px; text-transform: uppercase;">Inquired Products:</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        {items_html}
                    </ul>
                </div>

                <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-top: 20px;">
                    <h4 style="margin: 0 0 8px; color: #1e40af; font-size: 14px;">Need Immediate Assistance?</h4>
                    <p style="margin: 0; font-size: 13px; color: #1e3a8a; line-height: 1.5;">
                        Reach our sales engineers directly on WhatsApp or Call:<br>
                        <strong>Phone / WhatsApp:</strong> +91 83208 21579<br>
                        <strong>Email:</strong> <a href="mailto:divya.trading06@gmail.com" style="color: #0052CC;">divya.trading06@gmail.com</a>
                    </p>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 14px; text-align: center; font-size: 12px; color: #64748b;">
                15, Nageshwar Estate, Opp. Jawaharnagar - Gulabnagar Road, Nr. Amraiwadi A.E.C., Ahmedabad, Gujarat, India
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(subject, [inquiry.email], html, config)


def send_password_reset_email(email, customer_name, reset_url, config):
    """
    Sends a secure password reset link to customer email.
    """
    subject = "Reset Your Password - Divya Trading Co. Customer Portal"
    greeting_name = customer_name or 'Valued Customer'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #0A2540; padding: 28px 24px; text-align: center; border-bottom: 4px solid #0052CC;">
                <h2 style="color: #ffffff; margin: 0; font-size: 22px; letter-spacing: 0.5px;">DIVYA TRADING CO.</h2>
                <p style="color: #93c5fd; margin: 6px 0 0; font-size: 13px;">Customer Portal Password Assistance</p>
            </div>
            <div style="padding: 32px 28px;">
                <p style="font-size: 15px; color: #1e293b; margin-top: 0;">Hello <strong>{greeting_name}</strong>,</p>
                <p style="font-size: 14px; color: #475569; line-height: 1.6;">
                    We received a request to reset the password for your customer account at Divya Trading Co. Click the button below to set a new password:
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="display: inline-block; background: #0052CC; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 6px; font-weight: 700; font-size: 14px; letter-spacing: 0.5px; box-shadow: 0 3px 8px rgba(0,82,204,0.3);">
                        Reset My Password
                    </a>
                </div>

                <p style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 20px;">
                    This password reset link is valid for <strong>24 hours</strong>. If you did not request this, please disregard this email and your account password will remain unchanged.
                </p>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px 16px; font-size: 12px; color: #64748b; word-break: break-all;">
                    If the button doesn't work, copy and paste this link in your browser:<br>
                    <a href="{reset_url}" style="color: #0052CC;">{reset_url}</a>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b;">
                Divya Trading Co. · 15, Nageshwar Estate, Ahmedabad, Gujarat, India<br>
                Direct Support WhatsApp: +91 83208 21579
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(subject, [email], html, config)


def send_database_backup_email(backup_json_str, filename, config, recipient_email='neelbarot585@gmail.com'):
    """
    Sends an automated email containing full database backup JSON as an attachment.
    """
    subject = f"[Database Backup] Divya Trading Co. System Backup - {datetime.utcnow().strftime('%Y-%m-%d')}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; padding: 24px; border: 1px solid #e2e8f0;">
            <h2 style="color: #0A2540; margin-top: 0;">Divya Trading Co. — Full System Backup</h2>
            <p style="color: #475569; font-size: 14px; line-height: 1.5;">
                Attached is the latest automated database backup generated on <strong>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</strong>.
            </p>
            <p style="color: #475569; font-size: 14px;">
                <strong>Backup Contents:</strong>
            </p>
            <ul style="color: #334155; font-size: 13px; line-height: 1.6;">
                <li>All 24+ Precision Spare Products & Specifications</li>
                <li>Product Categories & Rotary Machine Makes</li>
                <li>Customer Registered Accounts & Contact Info</li>
                <li>Inquiries, Quotes & Status History</li>
                <li>Website CMS Settings & Brand Configurations</li>
            </ul>
            <p style="font-size: 12px; color: #94a3b8; margin-top: 20px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
                Auto-generated by Divya Trading Co. Production Cloud System.
            </p>
        </div>
    </body>
    </html>
    """
    
    sender = config.get('MAIL_DEFAULT_SENDER') or 'divya.trading06@gmail.com'
    mail_server = config.get('MAIL_SERVER')
    mail_port = config.get('MAIL_PORT', 587)
    username = config.get('MAIL_USERNAME')
    password = config.get('MAIL_PASSWORD')
    use_tls = config.get('MAIL_USE_TLS', True)
    
    if not username or not password:
        logger.info(f"[SIMULATED BACKUP EMAIL] To: {recipient_email} | File: {filename} ({len(backup_json_str)} bytes)")
        return True, "Backup generated and logged (Configure SMTP in settings for live inbox delivery)"
        
    try:
        from email.mime.application import MIMEApplication
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = f"Divya Trading Co. <{sender}>"
        msg['To'] = recipient_email
        
        msg.attach(MIMEText(html, 'html'))
        
        # Attach backup JSON
        part = MIMEApplication(backup_json_str.encode('utf-8'), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)
        
        if config.get('MAIL_USE_SSL'):
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=20)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=20)
            if use_tls:
                server.starttls()
                
        server.login(username, password)
        server.sendmail(sender, [recipient_email], msg.as_string())
        server.quit()
        return True, f"Backup successfully emailed to {recipient_email}"
    except Exception as e:
        logger.error(f"[BACKUP EMAIL ERROR] {str(e)}")
        return False, str(e)


def send_custom_customer_email(recipient_email, subject, message_body, config, customer_name=None, inquiry_number=None, cc=None, attachments=None):
    """
    Sends a beautifully formatted custom email to a customer with official DTC branding.
    Supports paragraphs, line breaks, optional inquiry tag, attachments, and clean contact details.
    """
    greeting_name = customer_name or 'Valued Customer'
    
    # Format line breaks and paragraphs in body if plain text passed
    if '<p>' not in message_body and '<br>' not in message_body and '<div>' not in message_body:
        formatted_body = ''.join([f"<p style='margin:0 0 14px; line-height:1.6;'>{p.strip()}</p>" for p in message_body.split('\n\n') if p.strip()])
        formatted_body = formatted_body.replace('\n', '<br>')
    else:
        formatted_body = message_body

    inquiry_badge = f"""
    <div style="display: inline-block; background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; margin-bottom: 16px;">
        Reference Inquiry #{inquiry_number}
    </div>
    """ if inquiry_number else ""

    attachment_badge = ""
    if attachments:
        attachment_names = [a.get('filename') if isinstance(a, dict) else a[0] for a in attachments if a]
        attachment_badge = f"""
        <div style="background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 12px; margin: 16px 0; font-size: 12px; color: #334155;">
            <strong>Attached Files ({len(attachment_names)}):</strong> {', '.join(attachment_names)}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{subject}</title>
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #0A2540; padding: 26px 28px; text-align: center; border-bottom: 4px solid #0052CC;">
                <h2 style="color: #ffffff; margin: 0; font-size: 22px; letter-spacing: 0.5px;">DIVYA TRADING CO.</h2>
                <p style="color: #93c5fd; margin: 4px 0 0; font-size: 13px;">Precision Rotary Printing Machine Spares • Ahmedabad, India</p>
            </div>
            
            <div style="padding: 28px;">
                {inquiry_badge}
                
                <p style="font-size: 15px; color: #1e293b; margin-top: 0;">Dear <strong>{greeting_name}</strong>,</p>
                
                <div style="font-size: 14px; color: #334155; line-height: 1.6; margin: 18px 0;">
                    {formatted_body}
                </div>
                
                {attachment_badge}
                
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 26px 0 10px;">
                    <h4 style="margin: 0 0 10px; color: #0A2540; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Direct Sales & Engineering Support:</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #475569;">
                        <tr>
                            <td style="padding: 4px 0; width: 32%;"><strong>Phone / WhatsApp:</strong></td>
                            <td style="padding: 4px 0;"><a href="https://wa.me/918320821579" style="color: #0052CC; text-decoration: none; font-weight: 700;">+91 83208 21579</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Direct Email:</strong></td>
                            <td style="padding: 4px 0;"><a href="mailto:divya.trading06@gmail.com" style="color: #0052CC; text-decoration: none;">divya.trading06@gmail.com</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Works & Office:</strong></td>
                            <td style="padding: 4px 0;">15, Nageshwar Estate, Amraiwadi, Ahmedabad - 380026, Gujarat, India</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div style="background: #f1f5f9; padding: 14px 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
                Divya Trading Co. • Quality Industrial Printing Machine Spare Parts Since 1997<br>
                <a href="https://divyatradingco.com" style="color: #0052CC; text-decoration: none;">divyatradingco.com</a>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(subject, [recipient_email], html, config, cc=cc, attachments=attachments)


def send_customer_welcome_email(customer, temp_password=None, config=None):
    """
    Sends an automated, beautifully branded welcome email to newly registered
    or existing customers added via admin with account details and direct portal login link.
    """
    subject = f"Welcome to Divya Trading Co. Customer Portal — {customer.name}"
    company_name = customer.company_name or 'Textile Mill Partner'
    
    password_block = ""
    if temp_password:
        password_block = f"""
        <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 16px 20px; margin: 20px 0;">
            <p style="margin: 0 0 6px; color: #92400E; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Your Portal Login Credentials</p>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #78350F;">
                <tr>
                    <td style="padding: 4px 0; width: 35%; font-weight: 600;">Login Email:</td>
                    <td style="padding: 4px 0; font-family: monospace; font-size: 15px;"><strong>{customer.email}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: 600;">Initial Password:</td>
                    <td style="padding: 4px 0; font-family: monospace; font-size: 15px; color: #B45309;"><strong>{temp_password}</strong></td>
                </tr>
            </table>
            <p style="margin: 8px 0 0; font-size: 12px; color: #92400E;">
                You can change this password at any time from your customer dashboard.
            </p>
        </div>
        """
        
    portal_url = "https://divyatradingco.com/customer/login"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to Divya Trading Co.</title>
    </head>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
        <div style="max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #0A2540; padding: 30px 28px; text-align: center; border-bottom: 4px solid #0052CC;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 0.5px;">DIVYA TRADING CO.</h1>
                <p style="color: #93c5fd; margin: 6px 0 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Precision Rotary Printing Machine Spares • Since 1997</p>
            </div>
            
            <div style="padding: 32px 28px;">
                <div style="background: #EFF6FF; border-left: 4px solid #0052CC; padding: 12px 18px; border-radius: 4px; margin-bottom: 24px;">
                    <span style="font-size: 13px; font-weight: 700; color: #1E40AF;">B2B CUSTOMER ACCOUNT ACTIVATED</span>
                </div>
                
                <p style="font-size: 16px; color: #0F172A; margin-top: 0;">Dear <strong>{customer.name}</strong> ({company_name}),</p>
                
                <p style="font-size: 14px; color: #334155; line-height: 1.6;">
                    Welcome to <strong>Divya Trading Co.</strong>! We are pleased to confirm that your customer account has been successfully set up on our B2B procurement portal.
                </p>
                
                {password_block}
                
                <div style="text-align: center; margin: 28px 0;">
                    <a href="{portal_url}" style="display: inline-block; background: #0052CC; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 700; font-size: 15px; letter-spacing: 0.5px; box-shadow: 0 4px 12px rgba(0,82,204,0.3);">
                        Access Customer Portal &rarr;
                    </a>
                </div>

                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 20px; margin: 26px 0;">
                    <h3 style="margin: 0 0 12px; color: #0A2540; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">What You Can Do on Your Portal:</h3>
                    <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #475569; line-height: 1.8;">
                        <li><strong>Track Your RFQs & Quotations:</strong> View real-time pricing, delivery timelines, and proforma status.</li>
                        <li><strong>One-Click Reorders:</strong> Quickly request quotes for Stormac, Laxmi, Stork RD-4, Pegasus, Zimmer & Reggiani machine spares.</li>
                        <li><strong>Order Repeat Gears & Screen Heads:</strong> Specify 64R, 81.9R, 91.4R, 101.8R repeat sizes directly online.</li>
                        <li><strong>Direct Engineering Support:</strong> Chat or message our technical team for custom CNC precision drawings.</li>
                    </ul>
                </div>
                
                <div style="background: #F1F5F9; border-radius: 8px; padding: 18px; margin-top: 24px;">
                    <h4 style="margin: 0 0 10px; color: #0A2540; font-size: 13px; text-transform: uppercase;">Direct Sales & WhatsApp Contact:</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #475569;">
                        <tr>
                            <td style="padding: 4px 0; width: 32%;"><strong>Phone / WhatsApp:</strong></td>
                            <td style="padding: 4px 0;"><a href="https://wa.me/918320821579" style="color: #16a34a; text-decoration: none; font-weight: 700;">+91 83208 21579</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Direct Email:</strong></td>
                            <td style="padding: 4px 0;"><a href="mailto:divya.trading06@gmail.com" style="color: #0052CC; text-decoration: none;">divya.trading06@gmail.com</a></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0;"><strong>Works Address:</strong></td>
                            <td style="padding: 4px 0;">15, Nageshwar Estate, Amraiwadi, Ahmedabad - 380026, Gujarat, India</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div style="background: #0A2540; padding: 16px 20px; text-align: center; font-size: 12px; color: #94A3B8;">
                Divya Trading Co. • Serving Leading Textile Mills Across India & Worldwide Since 1997<br>
                <a href="https://divyatradingco.com" style="color: #60A5FA; text-decoration: none;">https://divyatradingco.com</a>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(subject, [customer.email], html, config)

