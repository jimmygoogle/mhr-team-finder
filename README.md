# MHR Team Finder

[MyHockeyRankings](https://myhockeyrankings.com/)

This project is based on weekly data from [MyHockeyRankings](https://myhockeyrankings.com/) as a tool for people to find organizations within a defined area based on certain criteria. This can be used for scheduling and other purposes. The data is loaded from Postgres into Mapbox and filterable based on user selections.

## Demo

You can see a demo [here](http://www.itsawesomebaby.com/mhr)

Load DB from dump:

```
scp /Users/jbutler/dump.sql jbutler@192.168.86.130:/tmp/
docker exec -i mhr-team-finder-db-1 psql -U mhr_user -d postgres < /tmp/dump.sql
```