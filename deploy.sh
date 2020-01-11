#!/bin/bash

# GRG-bot: provide GRGs for maps via a discord bot
# Copyright © 2019, 2020 132nd.Professor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

set -e

echo commit: $(git rev-parse --short HEAD) > app/version.txt
git log | head -n3 | tail -n1 >> app/version.txt
echo "build:  $(LANG=en_US date '+%a %b %d %H:%M:%S %Y %z')" >> app/version.txt
sudo docker-compose build
sudo docker-compose up -d 
