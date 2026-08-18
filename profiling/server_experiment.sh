systemd-inhibit --what=sleep --why="stress-ng experiment" \
ssh <REMOTE_USER>@<REMOTE_HOST> 'cd /tmp && bash -s' < experiment.sh \
| tee -a ~/server_results.csv
