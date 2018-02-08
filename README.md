# Asterisk OwnCloud Whitelist

Asterisk OwnCloud Whitelist is a AGI script for Asterisk IP PBX to implement whitelist functionality and terminate 
unwanted calls like marketing, loan collectors, prankers, etc.


## Usage

1. Configure shared contact list at OwnCloud. Specify blacklist category for blacklisted contacts.
2. Prepare directory with autoanswer messages for blacklisted contacts - the script will randomly play sound on blacklisted call
3. Make asterisk-owncloud-whitelist.py executable, put the file into agi-bin Asterisk directory
4. Add the new extension to extensions.conf
~~~~
exten => 1234,1,AGI(asterisk-owncloud-whitelist.py,"owncloud.example.com","/remote.php/carddav/addressbooks/myusername/default","myusername","mypass","blacklist_sounds_subdirectory","blacklist_category")
~~~~
5. Restart Asterisk
6. After testing Asterisk redirect incoming calls to extension. For example, some cell operators provide additional service to assign SIP account to the MSISDN number


## Author and License

Copyright (C) 2018 667bdrm
Dual licensed under GNU General Public License 2 and commercial license
Commercial license available by request
