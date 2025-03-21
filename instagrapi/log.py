from instagrapi import Client
from instagrapi.exceptions import(LoginRequired)

cl = Client()
cl.login ("rjlinsta","G0sling!")
cl.dump_settings("rjlinsta.json")

