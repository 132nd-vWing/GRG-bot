FROM archlinux/base:latest

WORKDIR /tmp

RUN pacman -Syu --needed --noconfirm wget grep python-pip tar imagemagick ghostscript
RUN pip install discord.py && rm -rf /root/.cache/pip
RUN wget --quiet http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xf install-tl-unx.tar.gz
ADD texlive.profile /tmp/
RUN cd install-tl-2019* && ./install-tl -profile ../texlive.profile && rm -rf /tmp/* 
RUN /usr/local/texlive/2019/bin/x86_64-linux/tlmgr install standalone xkeyval fp adjustbox pgf collectbox xcolor tex-gyre
ENV PATH="/usr/local/texlive/2019/bin/x86_64-linux:${PATH}"
RUN rm /etc/ImageMagick-7/policy.xml
# Test the latex installation
USER nobody
ADD --chown=nobody:nobody grg.sty grg-test.tex /tmp/
RUN /usr/local/texlive/2019/bin/x86_64-linux/pdflatex -shell-escape grg-test.tex && rm -rf /tmp/* 

WORKDIR /app
ADD --chown=nobody:nobody main.py grg.sty config.py /app/

CMD ["python", "main.py"]

