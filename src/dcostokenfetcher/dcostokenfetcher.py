#!/usr/bin/env python3
# Copyright (c) 2019 Martijn Dekkers, D2iQ.
# Licensed under the Apache 2.0 License
# Martijn Dekkers <mdekkers@d2iq.com>

import json
import click
import requests
import warnings
import jwt
import datetime
warnings.filterwarnings("ignore")


def print_help(ctx, param, value):
    if value is False:
        return
    click.echo(ctx.get_help())
    ctx.exit()


@click.command()
@click.option(
    '--cluster',
    '-c',
    default='https://master.mesos',
    help='URL for the cluster'
)
@click.option(
    '--username',
    '-u',
    help='The username to fetch the JWT token for'
)
@click.option(
    '--userkey',
    '-k',
    help='The private key to use.',
)
@click.option(
    '--sasecret',
    '-s',
    help='Path to the sa-secret in the secret store. Use when running in a container. Either this option, or -k -c must be used'
)
@click.option(
    '--time',
    '-t',
    required=True,
    type=int,
    help='Time in seconds the token should be valid for'
)
@click.option(
    '--output',
    '-o',
    type=click.Choice(
        ['file',
         'screen'],
        case_sensitive=False
    ),
    default='screen',
    help='How to output the generated token. Options are "file" to write a "dcostoken" file in the current directory, or "screen" to echo to screen. Defaults to screen'
)
@click.option(
    '--help',
    '-h',
    is_flag=True,
    expose_value=False,
    is_eager=False,
    callback=print_help,
    help="Print help message"
)
def dcostokenfetcher(cluster, username, userkey, output, sasecret, time):
    """This program will fetch an authentication token from a DC/OS cluster"""

    # We can get the sa-secret JSON from the Mesos sandbox if defined.
    # This is a JSON file that contains everything we need to get a JWT
    if sasecret:
        with open(sasecret, "r") as f:
            secretjson = json.load(f)
            username = secretjson['uid']
            private_key = secretjson['private_key']

    else:
        keyfile = open(userkey, "r")
        private_key = keyfile.read()

    thetoken = jwt.encode(
        {"uid": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=time)},
        private_key, algorithm='RS256'
    )

    logintoken = thetoken.decode("utf-8")

    headers = {'Content-Type': 'application/json'}
    theusername = '"' + username + '"'
    thelogintoken = '"' + logintoken + '"'
    thepayload = '{"uid": ' + theusername + ', ' + '"token" :' + thelogintoken + '}'

    payload = thepayload
    api_endpoint = '/acs/api/v1/auth/login'

    api = cluster + api_endpoint

    tokenreturn = requests.post(url=api, headers=headers, data=payload, verify=False)

    token_dict = json.loads(tokenreturn.text)

    if 'token' in token_dict:
        if output == 'screen':
            click.echo(token_dict['token'])
        elif output == 'file':
            outfile = open("dcostoken", "w+")
            outfile.write(token_dict['token'])
            outfile.close()
        return
    else:
        click.echo('An error occured. Server response:')
        click.echo(tokenreturn.text)
        return


def main():
    dcostokenfetcher()


main()
