import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('EmailService')

# In-memory log of sent/attempted emails for admin audit
EMAIL_ACTIVITY_LOGS = []

def send_email(subject, recipients, html_content, config):
    """
    Sends an email using the SMTP settings provided in config.
    Logs success or failure gracefully.
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if not isinstance(recipients, list):
        recipients = [r.strip() for r in recipients.split(',') if r.strip()]
        
    sender = config.get('MAIL_DEFAULT_SENDER') or 'divya.trading06@gmail.com'
    mail_server = config.get('MAIL_SERVER')
    mail_port = config.get('MAIL_PORT', 587)
    username = config.get('MAIL_USERNAME')
    password = config.get('MAIL_PASSWORD')
    use_tls = config.get('MAIL_USE_TLS', True)
    
    log_entry = {
        'timestamp': timestamp,
        'subject': subject,
        'recipients': recipients,
        'sender': sender,
        'status': 'pending',
        'error': None
    }
    
    # Check if SMTP credentials are provided
    if not username or not password:
        log_entry['status'] = 'simulated'
        log_entry['note'] = 'SMTP credentials not configured in .env. Logged simulated email.'
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        logger.info(f"[SIMULATED EMAIL] To: {recipients} | Subject: {subject}")
        return True, "Email logged (Simulated Mode - configure SMTP in admin/env for live delivery)"
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"Divya Trading Co. <{sender}>"
        msg['To'] = ", ".join(recipients)
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        if config.get('MAIL_USE_SSL'):
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=15)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=15)
            if use_tls:
                server.starttls()
                
        server.login(username, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        
        log_entry['status'] = 'sent'
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        logger.info(f"[EMAIL SENT] To: {recipients} | Subject: {subject}")
        return True, "Email sent successfully"
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed sending to {recipients}: {str(e)}")
        log_entry['status'] = 'failed'
        log_entry['error'] = str(e)
        EMAIL_ACTIVITY_LOGS.append(log_entry)
        return False, str(e)


def notify_admin_new_inquiry(inquiry, config):
    """
    Sends email notification to the DTC admin team when a new inquiry arrives.
    """
    admin_emails = config.get('ADMIN_NOTIFICATION_EMAIL', 'divya.trading06@gmail.com,neelbarot585@gmail.com')
    subject = f"🔔 [New Inquiry #{inquiry.inquiry_number}] from {inquiry.customer_name} ({inquiry.company_name or 'Individual'})"
    
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
                            <a href="https://wa.me/{inquiry.phone.replace('+', '').replace(' ', '')}" style="color: #16a34a; text-decoration: none;">{inquiry.phone} 💬 (WhatsApp)</a>
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
                        📞 <strong>+91 83208 21579</strong> / <strong>+91 94260 64807</strong><br>
                        ✉️ <a href="mailto:divya.trading06@gmail.com" style="color: #0052CC;">divya.trading06@gmail.com</a>
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
