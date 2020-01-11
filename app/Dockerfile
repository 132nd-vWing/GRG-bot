# GRG-bot: provide GRGs for maps via a discord bot
# Copyright © 2019 132nd.Professor
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

# bootstrap the musl-version of pdflatex on ubuntu, since the texlive installer doesn't run out-of-the-box on alpine
# the final image runs on alpine
FROM ubuntu:disco AS builder

WORKDIR /tmp
ADD texlive.profile /tmp/
RUN apt update && apt install -y perl wget fontconfig && apt clean && \
    wget --quiet http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz && \
    tar -xf install-tl-unx.tar.gz && \
    cd install-tl-2020* && ./install-tl -repository ctan -profile ../texlive.profile && rm -rf /tmp/*
RUN /usr/local/texlive/2019/bin/x86_64-linux/tlmgr --repository ctan install \
    adjustbox \
    collectbox \
    epstopdf-pkg \
    fp \
    graphics \
    graphics-def \
    kvsetkeys \
    latex \
    latex-bin \
    ltxcmds \
    oberdiek \
    pdftex \
    pgf \
    standalone \
    tex-gyre \
    xcolor \
    xkeyval \
    && \
# we needed the glibc version only for bootstrapping
    rm -rf /usr/local/texlive/2019/bin/x86_64-linux

FROM alpine:latest AS final

COPY --from=builder /usr/local/texlive/ /usr/local/texlive
RUN apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    python3 \
    python3-dev \
    imagemagick \
    ghostscript \
    p7zip \
    && pip3 install discord \
    && rm -rf /root/.cache/pip
ENV PATH="/usr/local/texlive/2019/bin/x86_64-linuxmusl:${PATH}"

FROM final AS tester
WORKDIR /tmp
ADD --chown=nobody:nobody grg.sty grg-test.tex QESHM_airfield.png /tmp/
RUN /usr/bin/python3 -c 'import discord' && convert -version && gs -v && \
    pdflatex -halt-on-error -shell-escape grg-test.tex && rm -rf /tmp/*

FROM final
WORKDIR /app
USER nobody
ADD --chown=nobody:nobody main.py arg.py exceptions.py help.py config.py grg.sty version.txt /app/

CMD ["python3", "main.py"]

