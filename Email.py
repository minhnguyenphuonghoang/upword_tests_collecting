#!/usr/local/bin/python
# -*- coding: utf-8 -*-


import imaplib
import email
import re
from email.header import decode_header
import time 

"""
@Author: Minh.nguyen
@Created Date: Friday August 14, 2015
"""


class Email:

    def __init__(self):
        self.conn = None

    def connect_to_email(self, username, password, domain = 'imap.gmail.com', ssl=True):
        if ssl:
            self.conn = imaplib.IMAP4_SSL(domain)
        else:
            self.conn = imaplib.IMAP4(domain)
        self.conn.login(username, password)

    def close_connection (self):
        self.conn.close()
        self.conn.logout()
        
    def get_all_links(self, email_uid, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        result, data = self.conn.uid('search', None, "ALL")
        email_uids = data[0].split()
        
        if email_uid not in email_uids:
            assert False, "Your email id: %d doesn't exist on %s" % (email_uid, label)



        result, email_data = self.conn.uid('fetch', email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        for part in email_message.walk():
            if part.get_content_type() == "text/html":
                body = part.get_payload(decode=True)
                save_string = ""
                save_string+=body.decode('utf-8')
            else:
                continue

        urls = re.findall(r'href=[\'"]?([^\'" >]+)', save_string)
        return urls



    def get_a_link_in_email(self, email_uid, expected_link, label='inbox'):
        """
        Get a link in email by using:
        - index
        - link text

        Arguments: 
        - email_uid: which email do you want to get link
        - expected_link: index or link_text

        Return:
        - url
        """

        all_links = self.get_all_links(email_uid, label)
        

        try:
            expected_link = int(expected_link)
        except ValueError:
            expected_link = str(expected_link)

        type_of_link = type(expected_link)

        if(type_of_link == int):
            try:
                return all_links[expected_link]
            except IndexError:
                assert False, 'Email contains only %d links while you are\
                 expecting link at index: %d' % (len(all_links), expected_link)

        elif(type_of_link == str or type_of_link == unicode):        
            print "not implemented"
            # for item in all_links:
            #     if expected_link in item: 
            #         return item
            # assert False, "Email doesn't contain any link with link text: %s" % expected_link

        else:
            assert False, 'Unexpected argument type: %s' % type_of_link

# review here


    def get_body_content(self, index=-1, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        result, data = self.conn.uid('search', None, "ALL")      
        try:
            email_uid = data[0].split()[index]
        except IndexError:
            return None 
        result, email_data = self.conn.uid('fetch', email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        for part in email_message.walk():
            if part.get_content_type() == "text/html":
                body = part.get_payload(decode=True)
                save_string = ""
                save_string+=body.decode('utf-8')
            else:
                continue      
        return save_string

    def get_email_subject(self, index=-1, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        result, data = self.conn.uid('search', None, "ALL")
        try:
            email_uid = data[0].split()[index]
        except IndexError:
            return None
        result, email_data = self.conn.uid('fetch', email_uid, '(RFC822)')
        raw_email = email_data[0][1]
        
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        subject = decode_header(email_message['Subject'])        
        return subject[0][0]
    
    def delete_all_email(self, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        self.conn.recent()
        result, data = self.conn.search(None, "ALL") 
        for email_uid in data[0].split():
            self.conn.store(email_uid, '+FLAGS', '\\Deleted')

    def delete_an_email(self, email_uid, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        self.conn.recent()
        self.conn.uid('STORE', email_uid, '+FLAGS', r'\Deleted')

    def mark_an_email_as_read(self, email_uid, label='inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        self.conn.recent()
        self.conn.uid('STORE', email_uid, '+FLAGS', '\\Seen')
            

    def check_email_content(self, expected_content, compare_type=0, index=-1, label='inbox'):
        res = ''
        #compare type = 0: ralative comparition (check if content contains expected string)
        if(compare_type == 0):
            ## To fix case having 2 or more emails in mailbox ==> cannot get the expected email correctly,
            ## Mr Nguyen assumes subject is correct and do not need to check.
            ## I will base on expected subject to find expected email.
            try:
                index = self.get_email_index_by_subject(expected_content['subject'])
            except:
                assert False, "There is no email which has subject \"%s\"" % expected_content['subject']
            actual_subject = self.get_email_subject(index, label)            
            if not expected_content['subject'] in actual_subject: 
                res += "+ Subject does NOT match!\n"
                res += "     Actual subject: %s\n" % actual_subject
                res += "     Expected subject: %s\n" % expected_content['subject']
            actual_body = self.get_body_content(index, label)
            
            for item in expected_content['body']:
                if not item in actual_body: 
                    res += "+ Body does NOT contain: %s\n" % item

##            if (res != ''):
##                raise AssertionError(res)
            

            return res

        #compare_type = 1: absolute comparition (exactly the same)
        elif(compare_type == 1):
            print 'to be implemented'    
            return 'Function is being implemented, please choose compare_type = 0'
            
        else:
            return 'Invalid value for 2nd argument (compare_type)'

    def check_email_content_new(self, email_subject, *message):
        from bs4 import BeautifulSoup 
        import re

        try:
            index = self.get_email_index_by_subject(email_subject)
        except:
            assert False, "There is no email which has subject \"%s\"" % email_subject
        
        actual_body = self.get_body_content(index, "inbox")
        
        html_parse = BeautifulSoup(actual_body, "html.parser")
        actual_body = html_parse.get_text()
        # actual_body = re.sub(r"[\s\t\n]{1,1000}", " ", actual_body)
        actual_body = ' '.join(actual_body.strip().split())

        result = True
        errors = "Actual email body: \n%s\n" % actual_body
        if message is not None:
            for item in message:
                if not item in actual_body: 
                    result = False
                    errors += "+ Email body does not contain: %s\n" % item
        return result, errors



    def get_unseen_emails(self, label = 'inbox'):
        #select label
        self.conn.list()
        self.conn.select(label)

        result, data = self.conn.uid('search', None, "UNSEEN")
        return data[0].split()



    """
    @Edited by Minh.nguyen
    @Description: By default, if user inputs incorrect timeout, time_step, this keyword will assigned 120 to timeout, 30 to time_step
    """
    def wait_for_email(self, timeout=120, time_step=30):

        try:
            timeout = int(timeout)
        except:
            timeout = 120
        
        expected_time = timeout

        try:
            time_step = int(time_step)
        except:
            time_step = 30

        while(timeout >= time_step):            
            self.conn.recent()
            if len(self.get_unseen_emails()) > 0:
                return -1
            time.sleep(time_step)
            timeout -= time_step

        if(timeout >= 0):
            time.sleep(timeout)
            self.conn.recent()
            if len(self.get_unseen_emails()) > 0:
                return -1
        assert False, "No email arrives after %d!" % expected_time


    def wait_for_email_by_subject(self, subject='any',timeout=120, time_step=30):

        try:
            timeout = int(timeout)
        except:
            timeout = 120
        
        expected_time = timeout

        try:
            time_step = int(time_step)
        except:
            time_step = 30

        while(timeout >= time_step):            
            self.conn.recent()
            result, email_uids = self._get_unseen_email_by_subject(subject)

            if result==True:
                return email_uids

            time.sleep(time_step)
            timeout -= time_step

        if(timeout >= 0):
            time.sleep(timeout)
            self.conn.recent()
            result, email_uids = self._get_unseen_email_by_subject(subject)

            if result==True:
                return email_uids
        if subject == 'any':
            assert False, "No email arrives after %d!" % expected_time
        assert False, "No email with subject: '%s' arrives after %d!" % (subject, expected_time)
        
    def get_email_index_by_subject(self, subject, label = 'inbox'):
        self.conn.list()
        self.conn.select(label)

        #Matched email
        result, data = self.conn.uid('search', None, '(HEADER Subject "' + subject + '")')
        ##All email
        result, data2 = self.conn.uid('search', None, "ALL")
        
        return data2[0].split().index(data[0].split()[0])
        
        
    
    def _get_unseen_email_by_subject(self, subject='any', label = 'inbox'):
        
        #self.conn.list()
        self.conn.select(label, readonly=True)

        result, data = self.conn.uid('search', None, "UNSEEN")
        
        email_ids = data[0].split()

        if subject=='any':
            return True, email_ids

        for email_uid in email_ids:


            result, email_data = self.conn.uid('fetch', email_uid, '(RFC822)')

            curr_subject = decode_header(email.message_from_string(email_data[0][1].decode('utf-8'))['Subject'])

            if curr_subject[0][0] == subject:
                return True, email_uid

        return False, None
            
# if __name__ == '__main__':
#     email_test = Email()
#     email_test.connect_to_email('automationguru3@gmail.com','AutomationGuru')
#     uid = email_test.wait_for_email_by_subject("I've shared a file with you",10,3)
#     print uid
#     email_test.mark_an_email_as_read(uid)
#     # email_test.delete_an_email(uid)
#     email_test.close_connection()












