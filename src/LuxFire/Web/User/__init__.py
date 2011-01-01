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
import datetime, hashlib, pickle, random, time

from sqlalchemy.orm import eagerload	#@UnresolvedImport

from ...Database.Models.Role import Role
from ...Database.Models.User import User, EncryptedPasswordString
from ...Database.Models.UserSession import UserSession

from .. import LuxFireWeb
from ..bottle import request, response, redirect

#------------------------------------------------------------------------------ 
# Per-user management
#------------------------------------------------------------------------------ 
COOKIE_EXPIRE_DAYS = 7

def get_user_session():
	UserSession.delete_old_sessions()
	try:
		db = LuxFireWeb._db
		sess_id = request.COOKIES.get('session_id', '') #@UndefinedVariable
		user_session = db.query(UserSession).options(eagerload('user')).filter(UserSession.id==sess_id).one()
		user_session._data = pickle.loads(user_session.session_data)
		return user_session
	except:
		return None

# Provides @User.protected() decorator for access control
def protected():
	def decorator(func):
		def wrapper(*a, **ka):
			u_session = get_user_session()
			if not (u_session and u_session._data['logged_in'] == True):
				redirect('/user/login')
			return func(*a, **ka)
		return wrapper
	return decorator

@LuxFireWeb.route('/user/status')
@protected()
def user_status():
	u_session = get_user_session()
	if u_session and u_session._data['logged_in'] == True:
		return """Logged in as %s ! <a href="/user/logout">Log out</a>""" % u_session.user.email
	else:
		return """Logged out! <a href="/user/login">Log in</a>"""

@LuxFireWeb.route('/user/jobs')
@protected()
def user_jobs():
	return "[Table]"

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
			user_session.id = hashlib.md5( ('%s'%(time.time()*random.random())).encode() ).hexdigest()
			user_session.user_id = user.id
			user_session._data['logged_in'] = True
			user_session.session_data = pickle.dumps(user_session._data)
			user_session.expiry = datetime.timedelta(days=COOKIE_EXPIRE_DAYS) + datetime.datetime.now()
			db.add(user_session)
			response.set_cookie(
				'session_id',
				user_session.id,
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
	redirect('/user/status')


#------------------------------------------------------------------------------ 
# All users management
#------------------------------------------------------------------------------ 
@LuxFireWeb.route('/users')
@protected()
def user_index():
	return "[Table]"
