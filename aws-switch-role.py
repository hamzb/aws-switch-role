#!/usr/bin/env python
import sys
import argparse
import ConfigParser
import os
import boto3
import json

config_dir = os.path.expanduser("~") + '/.aws-switch-role'
config_file = config_dir + '/config'

def check_file(file_name):
	response = os.path.isfile(file_name)
	return response

def set_option(parser, section, option, value):
	if not value:
		if parser.has_option(section, option):
			parser.remove_option(section, option)
	else:
		parser.set(section, option, value)

def setDefault(args):
	response = check_file(config_file)
	if not response:
		print "Configuration file not found. Creating " + config_file
		if not os.path.isdir(config_dir):
			os.makedirs(config_dir)
		open(config_file,'w')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	if not parser.has_section('main'):
		parser.add_section('main')
	mfa_device = raw_input('Enter your default MFA device ID: ')
	iam_role = raw_input('Enter the default IAM role name you will be assuming: ')
	use_mfa = raw_input('Is MFA required by default? [yes/no]: ')
	default_profile = raw_input('Default IAM Profile: ')
	set_option(parser, 'main', 'mfa_device', mfa_device)
	set_option(parser, 'main', 'iam_role', iam_role)
	set_option(parser, 'main', 'use_mfa', use_mfa)
	set_option(parser, 'main', 'default_profile', default_profile)
	with open(config_file, 'w') as file:
		parser.write(file)


def setAccount(args):
	response = check_file(config_file)
	if not response:
		print 'Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters'
		exit(1)
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	account = raw_input('Enter the account name: ')
	if not account:
		raise ValueError('Account name is invalid')
	if not parser.has_section(account):
		parser.add_section(account)
	account_id = raw_input('Enter the account ID: ')
	if not account_id:
		raise ValueError('Account ID is invalid')
	set_option(parser, account, 'account_id', account_id)
	iam_role = raw_input('Enter the IAM role: ')
	set_option(parser, account, 'iam_role', iam_role)
	mfa_device = raw_input('Enter the mfa device: ')
	set_option(parser, account, 'mfa_device', mfa_device)
	use_mfa = raw_input('Does this account require mfa? [yes/no] ')
	set_option(parser, account, 'use_mfa', use_mfa)
	default_profile = raw_input('Default IAM Profile: ')
	set_option(parser, 'main', 'default_profile', default_profile)
	with open(config_file, 'wb') as file:
		parser.write(file)


def listAccount(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	account = args.acc
	if account == 'all':
		for section in parser.sections():
			print "[{0}]".format(section)
			for name, value in parser.items(section):
				print('{} = {}'.format(name, value))
			print "\n"
	else:
		if not parser.has_section(account):
			raise ValueError('Account does not exist')
		print "[{0}]".format(account)
		for name, value in parser.items(account):
				print('{} = {}'.format(name, value))



def removeAccount(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	account = args.acc
	if not account:
		raise ValueError('Account name is invalid')
	if not parser.has_section(account):
		raise ValueError('Account does not exist')
	else:
		parser.remove_section(account)
		with open(config_file, 'wb') as file:
			parser.write(file)

def assumeRole(args):
	response = check_file(config_file)
	if not response:
		raise ValueError('Couldnt find config file ' + config_file + '. Make sure to run aws-switch-role set-default to generate it and set the default parameters')
	parser = ConfigParser.SafeConfigParser()
	parser.read(config_file)
	iam_role = ''
	mfa_device = ''
	use_mfa = ''
	if parser.has_option('main', 'iam_role'):
		iam_role = parser.get('main', 'iam_role')
	if parser.has_option('main', 'mfa_device'):
		mfa_device = parser.get('main', 'mfa_device')
	if parser.has_option('main', 'use_mfa'):
		use_mfa = parser.get('main', 'use_mfa')
	if parser.has_option('main', 'default_profile'):
		default_profile = parser.get('main', 'default_profile')
	account = args.acc
	if not parser.has_section(account):
		raise ValueError('Account is invalid')
	if parser.has_option(account, 'iam_role'):
		iam_role = parser.get(account, 'iam_role')
	if parser.has_option(account, 'mfa_device'):
		mfa_device = parser.get(account, 'mfa_device')
	if parser.has_option(account, 'use_mfa'):
		use_mfa = parser.get(account, 'use_mfa')
	if parser.has_option(account, 'account_id'):
		account_id = parser.get(account, 'account_id')
	if parser.has_option(account, 'default_profile'):
		default_profile = parser.get(account, 'default_profile')

	role = 'arn:aws:iam::' + account_id + ':role/' + iam_role
	session = account
	iam_session = boto3.Session(profile_name=default_profile)
	client = iam_session.client('sts')
	if use_mfa != 'yes':
		try:
			response = client.assume_role(RoleArn=role, RoleSessionName=session)
			print json.dumps({'Credentials':{'Account': account, 'AccessKeyId': response['Credentials']['AccessKeyId'], 'SecretAccessKey': response['Credentials']['SecretAccessKey'], 'SessionToken': response['Credentials']['SessionToken']}})
		except Exception as err:
			raise ValueError(format(err))	
	else:
		if not mfa_device:
			raise ValueError("No MFA device found. If MFA is not required, make sure to turn it off. Otherwise, please set an MFA device in the main configuration section or in {0} account configuration".format(account))
		else:
			mfa_code = raw_input('Enter your MFA code: ')
			try:
				response = client.assume_role(RoleArn=role, RoleSessionName=session, SerialNumber=mfa_device, TokenCode=mfa_code)
				print json.dumps({'Credentials':{'Account': account, 'AccessKeyId': response['Credentials']['AccessKeyId'], 'SecretAccessKey': response['Credentials']['SecretAccessKey'], 'SessionToken': response['Credentials']['SessionToken']}})
			except Exception as err:
				raise ValueError(format(err))


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='sub-commands', description='actions to execute')

parser_set_default = subparsers.add_parser('set-default', help='sets default configuration')
parser_set_default.set_defaults(func=setDefault)

parser_list_account = subparsers.add_parser('list-account', help='lists the AWS accounts')
parser_list_account.set_defaults(func=listAccount)
parser_list_account.add_argument('--account', dest='acc', default='all', help='account you want to list its configuration. Values could be "all" or the account alias')

parser_set_account = subparsers.add_parser('set-account', help='Adds or modifys the settings of an AWS account')
parser_set_account.set_defaults(func=setAccount)

parser_remove_account = subparsers.add_parser('remove-account', help='removes an AWS account from configuration')
parser_remove_account.set_defaults(func=removeAccount)
parser_remove_account.add_argument('--account', dest='acc', default='all', help='account you want to list its configuration. Values could be "all" or the account alias')

parser_assume_role = subparsers.add_parser('assume-role', help='assumes the AWS role of the specified AWS account')
parser_assume_role.set_defaults(func=assumeRole)
parser_assume_role.add_argument('--account', dest='acc', help='Alias of the AWS Account you want to access')

args = parser.parse_args()
try:
	args.func(args)
except Exception as err:
	print str(err)
