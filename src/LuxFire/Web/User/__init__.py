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

from sqlalchemy.orm import eagerload

from ...Database.Models.User import User
from ...Database.Models.UserSession import UserSession

from .. import LuxFireWeb
from ..bottle import request, response, redirect

@LuxFireWeb.route('/user/test')
def user_test():
	count = int( request.COOKIES.get('counter', 0) ) #@UndefinedVariable
	count = '%s'%(count+1)
	response.set_cookie('counter', count)
	return count

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

@LuxFireWeb.route('/user/status')
def user_status():
	u_session = get_user_session()
	if u_session and u_session._data['logged_in'] == True:
		return """Logged in as %s ! <a href="/user/logout">Log out</a>""" % u_session.user.email
	else:
		return """Logged out! <a href="/user/login">Log in</a>"""

COOKIE_EXPIRE_DAYS = 7

@LuxFireWeb.route('/user/login')
def user_login():
	u_session = get_user_session()
	if not u_session:
		try:
			db = LuxFireWeb._db
			user = db.query(User).one()
			user_session = UserSession()
			user_session.id = hashlib.md5( ('%s'%(time.time()*random.random())).encode() ).hexdigest()
			user_session.user_id = user.id
			user_session._data['logged_in'] = True # TODO: add validation!
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
	redirect('/user/status')

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

