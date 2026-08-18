systemd-inhibit --what=sleep --why="Server Usage Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> 'bash -s' < monitor_usage.sh \
| tee -a ~/data/server_usage.csv
