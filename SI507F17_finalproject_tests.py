import unittest
from datetime import datetime, timedelta
from SI507F17_finalproject import *

print("BELOW IS TEST OUTPUT FOR FINAL PROJECT")

class Method_test(unittest.TestCase):
	def setUp(self):
		userlist = ['WOLF_STEVE']
		username = userlist[0]
		filename = '{0}.json'.format(username)
		user_url = 'https://api.dribbble.com/v1/users/{0}/shots'.format(username)
		shotsdict = get_user_dict(username, filename)
		shotsdict2 = get_user_dict('outcrowd', 'outcrowd.json')
		new_dict = get_sorted_dict_list(shotsdict)
		new_dict2 = get_sorted_dict_list(shotsdict2)
		user_list = execute_query("SELECT name from Users", 5)
		self.shot2 = shotsdict2
		self.dict1 = new_dict
		self.dict2 = new_dict2
		

	def test_user_dict(self):
		# print(str(shotsdict[0]).encode('utf-8'))
		self.assertIsInstance(shotsdict, list, 'Testing whether the data we got from the API is a list of dictionary.')
		self.assertEqual(shotsdict[0]['title'], 'Day full of working routine', 'Testing whether the title of the shots is the one we expected.')

	def test_user_dict_with_another_input(self):
		self.assertEqual(self.shot2[0]['title'], 'lifestyle landing')

	def test_cache_expired_method(self):
		now = datetime.now()
		four_days_ago = datetime.now() - timedelta(days=4)
		two_days_later = datetime.now() + timedelta(days=2)
		self.assertEqual(has_cache_expired(str(four_days_ago)), True, 'Testing if cache that expired can be noticed')
		self.assertEqual(has_cache_expired(str(two_days_later)), False, 'Testing if cache that expired can be noticed')

	def test_get_from_cache(self):
		self.assertIsInstance(get_from_cache(filename, username), list, 'Testing if cache can be retrived')
		self.assertIsInstance(get_from_cache('a', 'b'), type(None), 'Testing if wrong username will not trigger cache')

	def test_get_sorted_dict(self):
		self.assertEqual(str(new_dict[0]), 'Shot Title: Day full of working routine, Likes Count: 747, Views Count: 7196')

	def test_execute_query(self):
		self.assertEqual(user_list[1][0], 'outcrowd')

	def test_set_up_database_shots(self):
		cur.execute("""SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'shots' """)
		if cur.fetchone()[0] == 1:
			table_result = True
		else:
			table_result = False
		self.assertEqual(table_result, True, 'Testing if table can be created')

	def test_set_up_database_users(self):
		cur.execute("""SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' """)
		if cur.fetchone()[0] == 1:
			table_result = True
		else:
			table_result = False
		self.assertEqual(table_result, True, 'Testing if table can be created')

	def test_get_connection_and_cursor(self):
		self.assertIsInstance(conn, psycopg2.extensions.connection)
		self.assertIsInstance(cur, psycopg2.extras.DictCursor)

class Class_test(unittest.TestCase):
	def setUp(self):
		userlist = ['WOLF_STEVE']
		username = userlist[0]
		filename = '{0}.json'.format(username)
		user_url = 'https://api.dribbble.com/v1/users/{0}/shots'.format(username)
		shotsdict = get_user_dict(username, filename)
		shotsdict2 = get_user_dict('outcrowd', 'outcrowd.json')
		new_dict = get_sorted_dict_list(shotsdict)
		new_dict2 = get_sorted_dict_list(shotsdict2)
		user_list = execute_query("SELECT name from Users", 5)
		self.dict1 = new_dict
		self.dict2 = new_dict2

	def test_shots(self):
		self.assertEqual(new_dict[0].title, 'Day full of working routine')
		self.assertEqual(new_dict[0].url, 'https://cdn.dribbble.com/users/1925451/screenshots/4017216/workspacee_3.jpg')
		self.assertEqual(new_dict[0].likes, 747)
		self.assertEqual(new_dict[0].views, 7196)

	def test_shots_override(self):
		self.assertEqual(self.dict2[0].title, 'lifestyle landing')

	def test_shots_repr(self):
		self.assertEqual(new_dict[0].__repr__(), 'Shot Title: Day full of working routine, Likes Count: 747, Views Count: 7196')

	def test_shots_repr_override(self):
		self.assertEqual(self.dict2[0].__repr__(), 'Shot Title: lifestyle landing, Likes Count: 748, Views Count: 8573')

	def test_shots_contains(self):
		self.assertTrue(new_dict[0].__contains__('Day'))

	def test_shots_contains_override(self):
		self.assertTrue(self.dict2[0].__contains__('landing'))





if __name__ == '__main__':
	unittest.main(verbosity=2)