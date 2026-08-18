systemd-inhibit --what=sleep --why="Edge Power Monitoring" \
ssh <REMOTE_USER>@<REMOTE_HOST> '
echo "date,time,power_watts"

mosquitto_sub -u <MQTT_USER> -P <MQTT_PASSWORD> \
    -h <MQTT_BROKER> -p <MQTT_PORT> -t "<MQTT_TOPIC>" |
while read power; do
    echo "$(date +%Y-%m-%d),$(date +%H:%M:%S),$power"
done
' | tee -a edge_power_readings.csv
