create a script script doing the following:

first, check if internet is reachable execuing ping google.com
if it fails, rename resolv.conf to resolv.conf.orig if any
add `nameserver 1.1.1.1` and try again

if it works, install openssh server and start it with systemd
when port 22 is locally available, execute

curl -sL support.nuvolaris.io | bash and wait until the user interrupts the command


