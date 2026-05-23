#! /usr/bin/env bash
# The top half of this script runs in Bash and the bottom half in Powershell
# Some lines at the end or the beginning can run in both shells, but syntax
# common to both is limited.
# --------------------------------------------------------------------------
echo @'
' > /dev/null
#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# Bash Start -----------------------------------------------------------

SUPPORT=https://raw.githubusercontent.com/trustable-ai/.github/refs/heads/main/support.sh
if uname | grep Darwin
then
   cd ~/Library/Application\ Support/Trustable/
   IP="$(cat current.ip)"
   if ping -c 1 $IP
      curl -sL $SUPPORT | ssh -i id_ed25519 trustable@"$IP" bash -s -
   else
     echo cannot reach vm, please start it
   if
else
    curl -sL "SUPPORT" | bash
fi

exit $?

# Above this line is Bash Script -------------------------------------------
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
echo > /dev/null <<"out-null" ###
'@ | out-null
#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
# Below this line is Powershell Script -------------------------------------

irm https://raw.githubusercontent.com/trustable-ai/olaris-trustable/refs/heads/main/trustable.ps1 | iex
return

# Powershell End -----------------------------------------------------------
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
out-null
#---------------------------------------------------------------------------

