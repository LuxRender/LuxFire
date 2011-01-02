# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# LuxFire Distributed Rendering System
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#
"""
Interface for user session login/logout management
"""
import datetime, hashlib, pickle, random, sys, time

from sqlalchemy.orm import eagerload	#@UnresolvedImport

from ...Client import ClientException
from ...Database.Models.Queue import Queue
from ...Database.Models.Role import Role
from ...Database.Models.User import User, EncryptedPasswordString
from ...Database.Models.UserSession import UserSession

from ...Dispatcher.Client import DispatcherGroup

from .. import LuxFireWeb
if sys.version >= '3.0':
	from ..bottle.bottle3 import request, response, redirect
else:
	from ..bottle.bottle2 import request, response, redirect

def user_redirect(url, message):
	"""
	If this is an AJAX request, just return the message,
	otherwise perform a redirect().
	"""
	if request.is_ajax:
		return message
	else:
		redirect(url)

#------------------------------------------------------------------------------ 
# Per-user management
#------------------------------------------------------------------------------ 
COOKIE_EXPIRE_DAYS = 7

def get_user_session():
	UserSession.delete_old_sessions()
	try:
		db = LuxFireWeb._db
		sess_id = request.COOKIES.get('session_id', '') #@UndefinedVariable
		user_session = db.query(UserSession).options(eagerload('user')).filter(UserSession.sess_id==sess_id).one()
		user_session._data = pickle.loads(user_session.session_data)
		return user_session
	except:
		return None

# Provides @User.protected() decorator for access control
# roles[] is a list of roles the user must have to access this route.
# The user must hold any one of the roles given by name in the list.
def protected(roles=['login']):
	def decorator(func):
		def wrapper(*a, **ka):
			u_session = get_user_session()
			try:
				if not (u_session and u_session._data['logged_in'] == True):
					raise Exception('Not logged in')
				
				role_check = False
				for u_role in u_session.user.roles:
					for c_role in roles:
						if u_role.name == c_role:
							role_check = True
							break
					if role_check:
						break
				
				if not role_check:
					raise Exception('Insufficient privileges')
				
				return func(*a, **ka)
			except Exception as err:
				return user_redirect('/user/login', '%s'%err)
			
		return wrapper
	return decorator

@LuxFireWeb.get('/user/login')
def user_login_form():
	return LuxFireWeb._templater.get_template('user_login.html').render()

@LuxFireWeb.post('/user/login')
def user_login_process():
	u_session = get_user_session()
	if not u_session:
		try:
			email = request.forms.get('email') #@UndefinedVariable
			password = request.forms.get('password') #@UndefinedVariable
			
			db = LuxFireWeb._db
			user = db.query(User).filter(User.email==email).one()
			
			# TODO: User Role check for log in permission
			#  and user.roles.has(Role.name=='login')
			if not (user and EncryptedPasswordString.check_password(password, user.password)):
				redirect('/user/login')
			
			user_session = UserSession()
			user_session.sess_id = hashlib.md5( ('%s'%(time.time()*random.random())).encode() ).hexdigest()
			user_session.user_id = user.id
			user_session._data['logged_in'] = True
			user_session.session_data = pickle.dumps(user_session._data)
			user_session.expiry = datetime.timedelta(days=COOKIE_EXPIRE_DAYS) + datetime.datetime.now()
			db.add(user_session)
			response.set_cookie(
				'session_id',
				user_session.sess_id,
				path='/',
				expires=COOKIE_EXPIRE_DAYS*86400
			)
		except:
			pass
	redirect('/')

@LuxFireWeb.route('/user/logout')
def user_logout():
	u_session = get_user_session()
	if u_session:
		db = LuxFireWeb._db
		db.delete(u_session)
		response.set_cookie(
			'session_id',
			'',
			path='/',
			expires=-1
		)
	redirect('/')


@LuxFireWeb.route('/user/jobs')
@protected()
def user_jobs():
	u_session = get_user_session()
	uq = u_session.user.queue
	ur = u_session.user.results
	return LuxFireWeb._templater.get_template('user_jobs.html').render(
		user_queue=uq,
		user_queue_length=len(uq),
		user_results=ur,
		user_results_length=len(ur)
	)

@LuxFireWeb.post('/user/queue_finalise')
@protected()
def user_queue_finalise():
	try:
		dispatchers = DispatcherGroup()	# TODO: handle ClientException
	except ClientException as err:
		return {'error': '%s'%err}
	
	u_session = get_user_session()
	db = LuxFireWeb._db
	
	# Find the queue item
	q = db.query(Queue).filter(Queue.id==request.POST.get('q_id')).one()	#@UndefinedVariable
	
	# Check that the queue item is in the correct state and belongs to the correct
	# user and the dispatcher is available.
	if q.status=='NEW' and q.user_id == u_session.user.id and len(dispatchers) > 0:
		for dispatcher_name, dispatcher in dispatchers.items():	#@UnusedVariable
			break
		dispatcher.finalise_queue(u_session.user.id, q.jobname)
		
	return {}

@LuxFireWeb.post('/user/queue_dequeue')
@protected()
def user_queue_dequeue():
	try:
		dispatchers = DispatcherGroup()
	except ClientException as err:
		return {'error': '%s'%err}
	
	u_session = get_user_session()
	db = LuxFireWeb._db
	
	# Find the queue item
	q = db.query(Queue).filter(Queue.id==request.POST.get('q_id')).one()	#@UndefinedVariable
	
	# Check that the queue item is in the correct state and belongs to the correct
	# user and the dispatcher is available.
	if q.status=='READY' and q.user_id == u_session.user.id and len(dispatchers) > 0:
		for dispatcher_name, dispatcher in dispatchers.items():	#@UnusedVariable
			break
		dispatcher.abort_queue(u_session.user.id, q.jobname)
		
	return {}

@LuxFireWeb.post('/user/queue_new')
@protected()
def user_queue_new():
	try:
		dispatchers = DispatcherGroup()
		u_session = get_user_session()
		
		jobname = request.POST.get('jobname')	#@UndefinedVariable
		haltspp = int(request.POST.get('haltspp'))	#@UndefinedVariable
		halttime = int(request.POST.get('halttime'))	#@UndefinedVariable
		
		if not jobname or jobname == '':
			raise Exception('You must specify a job name.')
		
		if haltspp < 1 and halttime < 1:
			raise Exception('You must specify at least one halt condition.')
		
		if len(dispatchers) > 0:
			for dispatcher_name, dispatcher in dispatchers.items():	#@UnusedVariable
				break
			dispatcher.add_queue(u_session.user.id, jobname, haltspp, halttime)
		
		return {}
	except Exception as err:
		return {'error': '%s'%err}

@LuxFireWeb.post('/user/queue_upload')
@protected()
def user_queue_upload():
	try:
		u_session = get_user_session()
		db = LuxFireWeb._db
		q = db.query(Queue).filter(Queue.id==request.GET.get('q_id')).one()	#@UndefinedVariable
		filename = request.GET.get('qqfile')	#@UndefinedVariable
		filedata = request.body
		
		dispatchers = DispatcherGroup()
		if len(dispatchers) > 0:
			for dispatcher_name, dispatcher in dispatchers.items():	#@UnusedVariable
				break
			if dispatcher.add_file(u_session.user.id, q.jobname, filename, filedata.read()):
				return {'success':True}
		
		raise Exception('Error sending file to Dispatcher')
	except Exception as err:
		return {'success':False, 'error':'%s'%err}
#------------------------------------------------------------------------------ 
# All users management
#------------------------------------------------------------------------------ 
@LuxFireWeb.route('/users')
@protected()
def user_index():
	return "[Table]"
