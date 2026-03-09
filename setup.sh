#!/usr/bin/env bash

sudo bpftool map create /sys/fs/bpf/mnt_ns_set type hash key 8 value 4 entries 128 name mnt_ns_set flags 0

FILE=/sys/fs/bpf/mnt_ns_set
if [ $(printf '\1' | od -dAn) -eq 1 ]; then
    HOST_ENDIAN_CMD=tac
else
    HOST_ENDIAN_CMD=cat
fi

# ENTER MANUALLY IF MORE THAN ONE CONTAINER ACTIVE
CONTAINERID="$(docker ps -q | head -n 1)" 

NS_ID_HEX="$(printf '%016x' $(sudo stat -Lc '%i' /proc/$(docker inspect --format '{{.State.Pid}}' $CONTAINERID)/ns/mnt) | sed 's/.\{2\}/&\n/g' | $HOST_ENDIAN_CMD)"
sudo bpftool map update pinned $FILE key hex $NS_ID_HEX value hex 00 00 00 00 any
