# bootstrap the musl-version of pdflatex on ubuntu, since the texlive installer doesn't run out-of-the-box on alpine
# the final image runs on alpine
FROM ubuntu:disco AS builder

WORKDIR /tmp
ADD texlive.profile /tmp/
RUN apt update && apt install -y perl wget fontconfig && apt clean && \
    wget --quiet http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz && \
    tar -xf install-tl-unx.tar.gz && \
    cd install-tl-2019* && ./install-tl -profile ../texlive.profile && rm -rf /tmp/*  
RUN /usr/local/texlive/2019/bin/x86_64-linux/tlmgr install \
    latex-bin \
    pdftex \
    latex \
    standalone \
    xkeyval \
    fp \
    adjustbox \
    pgf \
    collectbox \
    xcolor \
    tex-gyre \
    oberdiek \
    ifluatex \
    graphics \
    graphics-def && \
# we needed the glibc version only for bootstrapping
    rm -rf /usr/local/texlive/2019/bin/x86_64-linux

FROM alpine:latest AS final

COPY --from=builder /usr/local/texlive/ /usr/local/texlive
RUN apk add --no-cache \
    python3 \
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
ADD --chown=nobody:nobody main.py arg.py help.py config.py grg.sty version.txt /app/
USER nobody

CMD ["python3", "main.py"]

