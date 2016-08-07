# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, url_for, redirect, jsonify
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('index.html')
	# return 'hello 2!'

@app.route('/send_email', methods=['POST'])
def send_email():
	name = request.form['name']
	phone = request.form['phone']
	ask_content = request.form['ask_content']
	print(request.form)
	if name == '' or phone == '' or ask_content == '':
		return '0'
	msg = MIMEText(name + '\n\n' + phone + '\n\n' + ask_content, _charset="utf-8")
	me = 'wlwkgus1994@gmail.com'
	from_ = 'www.mozart=magicflute.com'
	msg['Subject'] = 'Ask from mozart'
	msg['From'] = from_
	msg['To'] = me

	s = smtplib.SMTP('localhost', port=25)
	s.sendmail(from_, [me], msg.as_string())
	s.quit()
	return '1'

if __name__=='__main__':
	app.run(debug=True, host='0.0.0.0')
