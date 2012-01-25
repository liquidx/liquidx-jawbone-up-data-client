#!/usr/bin/python

from datetime import datetime, timedelta
import json
import logging
import time
import urllib
import urllib2

AUTH_URL = 'https://jawbone.com/user/signin/login'
BASE_URL = 'https://jawbone.com/nudge/api/'

HEADERS = {
  'User-Agent': 'Nudge/1.3.1 CFNetwork/548.0.4 Darwin/11.0.0',
  'x-nudge-platform': 'iPhone 4; 5.0.1',
}

class JawboneUp:
  def __init__(self, email, password):
    self.email = email
    self.password = password
    self.token = None
    self.user = {}
    self.request_count = 0
    
    self.auth(email, password)
    
  def backup(self):
    start_date = datetime(2011, 11, 1)
    end_date = datetime.now()
    backup_date = start_date
    
    while backup_date < end_date:
      start = backup_date
      end = backup_date + timedelta(days=1)
      backup_date = end # increment by one day.
      
      summary_date = start.strftime('%Y-%m-%d')
      print summary_date
      summary = self.get_daily_summary(summary_date)
      json.dump(summary, open('summary-%s.json' % summary_date, 'w'))
      
      start_epoch = int(time.mktime(start.timetuple()))
      end_epoch = int(time.mktime(end.timetuple()))
      activity = self.get_activity(start_epoch, end_epoch)
      json.dump(activity, open('activity-%s.json' % summary_date, 'w'))
      
      sleeps = self.get_sleeps(start_epoch, end_epoch)
      json.dump(activity, open('sleeps-%s.json' % summary_date, 'w'))
      if 'data' in sleeps and 'items' in sleeps['data']:
        for sleep in sleeps['data']['items']:
          sleep_xid = sleep['xid']
          sleep = self.get_sleep_detail(sleep_xid)
          json.dump(sleep, open('sleeps-%s-%s.json' % (summary_date, sleep_xid), 'w'))
          
      workouts = self.get_workouts(start_epoch, end_epoch)
      json.dump(activity, open('workouts-%s.json' % summary_date, 'w'))
      if 'data' in workouts and 'items' in workouts['data']:
        for workout in workouts['data']['items']:
          workout_xid = workout['xid']
          workout = self.get_workout_detail(workout_xid)
          json.dump(workout, open('workouts-%s-%s.json' % (summary_date, workout_xid), 'w'))

    
  def test(self):
    summary = self.get_daily_summary('2011-11-01')
    print summary
    
    start = datetime(2012, 1, 20)
    end = start + timedelta(days=1)
    start_epoch = int(time.mktime(start.timetuple()))
    end_epoch = int(time.mktime(end.timetuple()))
    
    activity = self.get_activity(start_epoch, end_epoch)
    print activity
      
    #sleeps = self.get_sleeps(start_epoch, end_epoch)
    #print sleeps
    #  for sleep_item in sleeps['data']['items']:
    #    self.get_sleep_detail(sleep_item['xid'])
    #    
    #  workouts = self.get_workouts(start_epoch, end_epoch)
    
  def auth(self, email, password):
    params = {'email': email, 'pwd': password, 'service': 'nudge'}
    req = urllib2.Request(AUTH_URL, urllib.urlencode(params))
    resp = urllib2.urlopen(req)
    resp_json = json.load(resp)
    if 'rc' in resp_json:
      self.token = resp_json.get('token')
      self.user = resp_json.get('user')
      logging.info('Authenticated.')
    else:
      logging.error('Unable to authenticate: %s' % resp_json)
      
  def request(self, path, params):
    headers = HEADERS
    headers['x-nudge-request-id'] = self.request_count
    self.request_count += 1
    headers['x-nudge-token'] = self.token
    req = urllib2.Request('%s%s?%s' % (BASE_URL, path, urllib.urlencode(params)), None, headers)
    return json.load(urllib2.urlopen(req))

  def get_daily_summary(self, date, timezone = 0):
    path = 'users/%s/healthCredits' % self.user['xid']
    params = {
      'date': date,
      'timezone': timezone,
      'move_goal': 0,
      'sleep_goal': 0,
      'eat_goal': 0,
      'check_levels': 1,
      '_token': self.token
    }
    resp = self.request(path, params)
    return resp
    
  def get_activity(self, start, end):
    path = 'users/%s/band' % self.user['xid']
    params = {
      'start_time': start,
      'end_time': end,
      '_token': self.token
    }
    try:
      resp = self.request(path, params)
    except urllib2.HTTPError, e:
      logging.error('Unable to fetch activity: %s' % e)
      return {}
    return resp
    
  def get_sleeps(self, start, end):
    path = 'users/%s/sleeps' % self.user['xid']
    params = {
      'start_time': start,
      'end_time': end,
      'limit': 100,
      '_token': self.token
    }
    resp = self.request(path, params)
    return resp
    
  def get_sleep_detail(self, xid):
    path = 'sleeps/%s/snapshot' % xid
    params = {
      '_token': self.token
    }
    resp = self.request(path, params)
    return resp
    
  def get_workouts(self, start, end):
    path = 'users/%s/workouts' % self.user['xid']
    params = {
      'start_time': start,
      'end_time': end,
      'limit': 100,
      '_token': self.token
    }
    resp = self.request(path, params)
    return resp  
      
  def get_workout_detail(self, xid):
    path = 'workouts/%s/snapshot' % xid
    params = {
      '_token': self.token
    }
    resp = self.request(path, params)
    return resp   
    
if __name__ == '__main__':
  import getpass
  password = getpass.getpass()
  up = JawboneUp('alastair@liquidx.net', password)
  up.backup()
  