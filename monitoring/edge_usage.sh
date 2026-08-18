systemd-inhibit --what=sleep --why="Edge Usage Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> 'bash -s' < monitorEdgeUsage.sh \
| tee -a edge_usage.csv
