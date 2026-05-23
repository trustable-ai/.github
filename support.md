
create a script script doing the following:

first, check if internet is reachable executing ping google.com
if it fails, rename resolv.conf to resolv.conf.orig if any
write a resolv.conf with `nameserver 1.1.1.1` and try again

if it works, install openssh server and start it with systemd
when port 22 is locally available, execute

curl -sL support.nuvolaris.io | bash and wait until the user interrupts the command

assume it is executed by an user with passwordless sudo and can be executed with piped stdin

