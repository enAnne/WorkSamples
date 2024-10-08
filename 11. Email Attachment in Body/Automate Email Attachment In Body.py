# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 18:02:23 2022

@author: eeann
"""

import imaplib
import os 
import email
from pdf2image import convert_from_path
from smtplib import SMTP
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import keyring

keyring.get_keyring()
keyring.set_password("Outlook", "gc_ngea@m1.com.sg", "jlnjvmyzfytgqcgg")

imap_server = "outlook.office365.com"
imap_user = "gc_ngea@m1.com.sg"
imap_password = keyring.get_password("Outlook", "gc_ngea@m1.com.sg")
folder='Test'
subject='Citi-M1 Card KPI update'
sender='no-reply@notification.thoughtspot.com'
download_folder=r"C:\Users\eeann\Email Attachments"
page = 1
mail = imaplib.IMAP4_SSL(imap_server,993)
(retcode, capabilities) = mail.login(imap_user,imap_password)
img_name = 'image1.png'

def get_email(imap_server, imap_user, imap_password, folder='INBOX', subject=None, sender=''):
    mail.select(folder)
    (retcode, messages) = mail.search(None, '(UNSEEN)', '(FROM "'+sender+'")', '(SUBJECT "'+subject+'")')
    
    msgs = []
    if retcode == "OK":
        for message in messages[0].split():
            try: 
                ret, data = mail.fetch(message,'(RFC822)')
            except:
                print("No new msgs to read.")
                mail.close_connection()
                exit()

            msg = email.message_from_string(data[0][1].decode('utf-8'))
            if isinstance(msg, str) == False:
                msgs.append(msg)
            #response, data = mail.store(message, '+FLAGS','\\Seen')

        return msgs

def save_attachment(msgs, download_folder="/tmp"):
    """
    Given a message, save its attachments to the specified
    download folder (default is /tmp)

    return: file path to attachment
    """
    for msg in msgs:
        file_path = "No attachment found."
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            filename = part.get_filename()
            if filename:
                file_path = os.path.join(download_folder, filename.replace(':',''))
                
                if not os.path.isfile(file_path):
                    fp = open(file_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
        return file_path

def convert_pdf_to_image(file_path):
    images = convert_from_path(file_path, 500, poppler_path=r'C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\11. Email Attachment in Body\poppler-0.68.0\bin')
    for i, image in enumerate(images):
        png_path = download_folder+'/image'+str(i)+'.png'
        image.save(png_path, "PNG")
    return png_path
            
def email_image(png_path, img_name):
    to_emails = ['gc_ngea@m1.com.sg', 'eeann.ng@gmail.com']
    
    # Create multipart MIME email
    email_message = MIMEMultipart()
    email_message.add_header('To', ', '.join(to_emails))
    email_message.add_header('From', imap_user)
    email_message.add_header('Subject', subject)
    
    # Create text (Cannot include text, this will cause embedded image to turn into attachment)
    #text_part = MIMEText("Hello there! \n \nHere's your weekly M1-Citibank KPI Updates. \n \n", 'plain')
    #email_message.attach(text_part)
    
    # Create image attachment (Must attach to be able to embed in HTML)
    with open(png_path, "rb") as fp:
        img = MIMEImage(fp.read())
    img.add_header("Content-ID", "<{}>".format(img_name))
    email_message.attach(img)
    
    # Embed image attachment in email html body
    html_part = MIMEText('<html><body><h5>Hello there! <br> <br>Here is your weekly M1-Citibank KPI Updates. <br> <br><img src="cid:'+img_name+'"  width=500 height=800/> <br> <br>Best regards,<br> DO Data Analytics Team</h5></body></html>', 'html')
    email_message.attach(html_part)
    
    # Connect, authenticate, and send mail
    context = ssl.create_default_context()
    with SMTP(imap_server, 587) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(imap_user, imap_password)
        server.sendmail(imap_user, to_emails, email_message.as_string())
    
msgs = get_email(imap_server, imap_user, imap_password, folder, subject, sender)        
file_path = save_attachment(msgs, download_folder)
png_path = convert_pdf_to_image(file_path)
email_image(png_path, img_name)


