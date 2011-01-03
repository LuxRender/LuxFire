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
import datetime, hashlib, random, sys, time

from sqlalchemy.orm import eagerload	#@UnresolvedImport

from ...Client import ClientException
from ...Database.Models.Queue import Queue
from ...Database.Models.Role import Role
from ...Database.Models.User import User, EncryptedPasswordString
from ...Database.Models.UserSession import UserSession

from ...Dispatcher.Client import DispatcherGroup

from .. import LuxFireWeb
if sys.version >= '3.0':
	from ..bottle.bottle3 import request, response, redirect	#@UnresolvedImport
else:
	from ..bottle.bottle2 import request, response, redirect	#@UnresolvedImport

def user_redirect(url, message):
	"""
	If this is an AJAX request, just return the message,
	otherwise perform a redirect().
	"""
	if request.is_ajax:
		return message
	else:
		redirect(url)

def find_dispatcher():
	ds = DispatcherGroup()
	for dn, d in ds.items(): #@UnusedVariable
		return d

#------------------------------------------------------------------------------ 
# Per-user management
#------------------------------------------------------------------------------ 
COOKIE_EXPIRE_DAYS = 7

# SESSION UTILS

def get_user_session():
	UserSession.delete_old_sessions()
	try:
		sess_id = request.COOKIES.get('session_id', '') #@UndefinedVariable
		user_session = LuxFireWeb._db.query(UserSession).options(eagerload('user')).filter(UserSession.sess_id==sess_id).one()
		return user_session
	except:
		raise ClientException('No active user session')

def create_session_key():
	return hashlib.md5( ('%s'%(time.time()*random.random())).encode() ).hexdigest()

def set_dispatcher_key():
	"""
	This method will set a key in the current user session
	so that method calls on the Dispatcher can verify that
	the commands came from a logged in user, and not from
	other network traffic pretending to be a user.
	
	I don't pretend that this is totally secure, but it is
	probably a bit better than nothing at all.
	
	Note, that just sending the existing session_id like a
	browser does is not secure at all, since it is the same
	for every request.
	"""
	
	u_session = get_user_session()
	dk = create_session_key()
	u_session.session_data['dispatcher_key'] = dk
	LuxFireWeb._db.add(u_session)
	LuxFireWeb._db.flush()
	
	return dk

# Provides @User.protected() decorator for access control
# roles[] is a list of roles the user must have to access this route.
# The user must hold any one of the roles given by name in the list.
def protected(roles=['login']):
	def decorator(func):
		def wrapper(*a, **ka):
			try:
				u_session = get_user_session()
				if not ('logged_in' in u_session.session_data.keys() and u_session.session_data['logged_in'] == True):
					raise ClientException('Not logged in')
				
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

def get_user_queue_item():
	"""Get the queue item belonging to the logged in user
	and with ID == GET['q_id']"""
	u_session = get_user_session()
	return LuxFireWeb._db.query(Queue).filter(Queue.user_id==u_session.user.id).filter(Queue.id==request.POST.get('q_id')).one()	#@UndefinedVariable

# ROUTES

@LuxFireWeb.get('/user/login')
def user_login_form():
	return LuxFireWeb._templater.get_template('user_login.html').render()

@LuxFireWeb.post('/user/login')
def user_login_process():
	try:
		u_session = get_user_session()	#@UnusedVariable
	except ClientException:
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
			user_session.sess_id = create_session_key()
			user_session.user_id = user.id
			user_session.session_data = {'logged_in':  True}
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
	finally:
		redirect('/')

@LuxFireWeb.route('/user/logout')
def user_logout():
	try:
		u_session = get_user_session()
		db = LuxFireWeb._db
		db.delete(u_session)
		response.set_cookie(
			'session_id',
			'',
			path='/',
			expires=-1
		)
	except ClientException: pass
	finally:
		redirect('/')

@LuxFireWeb.route('/user/jobs')
@protected()
def user_jobs():
	try:
		u_session = get_user_session()
		uq = u_session.user.queue
		ur = u_session.user.results
		return LuxFireWeb._templater.get_template('user_jobs.html').render(
			user_queue=uq,
			user_queue_length=len(uq),
			user_results=ur,
			user_results_length=len(ur)
		)
	except ClientException as err:
		return '%s' % err

@LuxFireWeb.post('/user/queue_finalise')
@protected()
def user_queue_finalise():
	try:
		dispatcher = find_dispatcher()
		
		# Find the queue item
		q = get_user_queue_item()
		
		# Check that the queue item is in the correct state.
		if q.status=='NEW':
			dispatcher.finalise_queue(q.user_id, set_dispatcher_key(), q.jobname)
		
		return {'success':True}
	except Exception as err:
		return {'error': '%s'%err}

@LuxFireWeb.post('/user/queue_dequeue')
@protected()
def user_queue_dequeue():
	try:
		dispatcher = find_dispatcher()
		
		# Find the queue item
		q = get_user_queue_item()
		
		# Check that the queue item is in the correct state.
		if q.status=='READY':
			dispatcher.abort_queue(q.user_id, set_dispatcher_key(), q.jobname)
			
		return {'success':True}
	except Exception as err:
		return {'error': '%s'%err}

@LuxFireWeb.post('/user/queue_new')
@protected()
def user_queue_new():
	try:
		dispatcher = find_dispatcher()
		u_session = get_user_session()
		
		jobname = request.POST.get('jobname')	#@UndefinedVariable
		haltspp = int(request.POST.get('haltspp'))	#@UndefinedVariable
		halttime = int(request.POST.get('halttime'))	#@UndefinedVariable
		
		if not jobname or jobname == '':
			raise Exception('You must specify a job name.')
		
		if haltspp < 1 and halttime < 1:
			raise Exception('You must specify at least one halt condition.')
		
		dispatcher.add_queue(u_session.user.id, set_dispatcher_key(), jobname, haltspp, halttime)
		
		return {'success':True}
	except Exception as err:
		return {'error': '%s'%err}

@LuxFireWeb.post('/user/queue_upload')
@protected()
def user_queue_upload():
	try:
		dispatcher = find_dispatcher()
		
		q = get_user_queue_item()
		filename = request.GET.get('qqfile')	#@UndefinedVariable
		filedata = request.body
		
		if dispatcher.add_file(q.user_id, set_dispatcher_key(), q.jobname, filename, filedata.read()):
			return {'success':True}
		
		raise Exception('Error sending file to Dispatcher')
	except Exception as err:
		return {'success':False, 'error':'%s'%err}

@LuxFireWeb.post('/user/queue_reset')
@protected()
def user_queue_reset():
	try:
		dispatcher = find_dispatcher()
		
		q = get_user_queue_item()
		
		dispatcher.reset_queue(q.user_id, set_dispatcher_key(), q.jobname)
		
		return {'success':True}
	except Exception as err:
		return {'success':False, 'error':'%s'%err}

#------------------------------------------------------------------------------ 
# All users management
#------------------------------------------------------------------------------ 
@LuxFireWeb.route('/users')
@protected()
def user_index():
	return "[Table]"
