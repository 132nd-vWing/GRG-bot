FROM archlinux/base

WORKDIR /root
ADD texlive.profile grg-test.tex /root/

RUN pacman -Sy --noconfirm wget grep
RUN pip3 install discord.py
RUN wget --quiet http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf install-tl-unx.tar.gz
RUN cd install-tl-2019* && ./install-tl -profile ../texlive.profile
RUN /usr/local/texlive/2019/bin/x86_64-linux/tlmgr install standalone xkeyval fp adjustbox pgf collectbox xcolor tex-gyre
WORKDIR /tmp
ENV PATH="/usr/local/texlive/2019/bin/x86_64-linux:${PATH}"
RUN ln -s /root/grg-test.tex .
ADD grg.sty /tmp
# Test the latex installation
RUN /usr/local/texlive/2019/bin/x86_64-linux/pdflatex grg-test.tex && rm -rf /tmp/* 

ADD main.py grg.sty config.py /app/
WORKDIR /app

ENTRYPOINT python3 main.py

