MPDProxy
========

MPDProxy is a MPD (http://www.musicpd.org) pseudo server which purpose
is to control multiple mpd servers using a single client.

The typical usage is controlling several audio stations (in several
rooms, or in the same one) at once, while preserving audio
synchronisation and audio quality. It supposes that all controlled
servers use the same database with the same file names.

This is an alternative to having one mpd server that streams its
content to the other ones.

Requirements
============
- Python 3.x (tested with python 3.3.5)
- MPD servers to control :p

Features
========

- most mpc protocol commands works (indeed, only a small portion are
  modified activelly by this software)

- will work with all files that are common in the databases of the
  controlled mpd servers even if the databases were not generated at
  the same time. For those familiar with mpd protocol, each song has a
  unique `SONGID` that depends on when it has been added in the database
  by the `update` command. Thus, if you control several servers, the
  same song may not have the same `SONGID` on all servers (actually this is
  even quite unlikely). The proxy manages its own `File<->SONGID` mapping
  and rewrites all mpd commands based on `SONGID`

- `idle` command is not implemented/forwarded. This may affect some
  clients that rely on this command.

- The MPD version announced by the proxy is the lowest version number
  of all controlled servers. This should make the clients to limit
  their command use to a subset that is understood by all controlled
  servers.

Usage
=====

The command has a help message that should be quite self-explanatory:

    usage: mpdproxy.py [-h] [-s SERVERS] [-b BIND]
    
    optional arguments:
      -h, --help            show this help message and exit
      -s SERVERS, --servers SERVERS
                            server to control using addr[:port] format. Can be
                            specified several times to control more servers
      -b BIND, --bind BIND  Bind address using the form addr[:port]. Defaults to
                            0.0.0.0:6601

Future features (hopefuly)
==========================

- `idle` command

- special handling of `outputs` command to select which servers to control/disable/enable

- Measurement of the delays delta between servers to try to
  synchronize them as much as possible. Yet, LAN and low latency is
  assumed thus no latency compensation is done.

