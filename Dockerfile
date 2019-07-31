FROM archlinux/base

WORKDIR /tmp

RUN pacman -Syu --noconfirm wget grep python-pip tar
RUN pip install discord.py
RUN wget --quiet http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf install-tl-unx.tar.gz
ADD texlive.profile /tmp/
RUN cd install-tl-2019* && ./install-tl -profile ../texlive.profile
RUN /usr/local/texlive/2019/bin/x86_64-linux/tlmgr install standalone xkeyval fp adjustbox pgf collectbox xcolor tex-gyre
ENV PATH="/usr/local/texlive/2019/bin/x86_64-linux:${PATH}"
# Test the latex installation
ADD grg.sty grg-test.tex /tmp/
RUN /usr/local/texlive/2019/bin/x86_64-linux/pdflatex grg-test.tex
RUN rm -rf /tmp/* /etc/imageMagick-7/policy.xml

WORKDIR /app
ADD main.py grg.sty config.py /app/

ENTRYPOINT python main.py

