systemd-inhibit --what=sleep --why="Server Usage Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> 'bash -s' < monitor_usage.sh \
| tee -a server_usage.csv
