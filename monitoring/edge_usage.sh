systemd-inhibit --what=sleep --why="Edge Usage Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> 'bash -s' < monitor_usage.sh \
| tee -a ~/data/edge_usage.csv
