# collects llc_usage, mbm_total_bytes, mbm_local_bytes per app
while true;do sleep 3;for file in $(find /sys/fs/resctrl/*/mon_data/*00 -type f); do echo "$file,$(date '+%Y-%m-%d %H:%M:%S'),$(cat $file)" | tee -a llc_mbm_usage.csv; done;done
