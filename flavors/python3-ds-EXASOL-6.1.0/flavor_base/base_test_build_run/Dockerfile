FROM {{language_deps}}

COPY --from={{base_test_deps}} /usr /usr
COPY --from={{base_test_deps}} /lib /lib
COPY --from={{base_test_deps}} /bin /bin
COPY --from={{base_test_deps}} /opt /opt
COPY --from={{base_test_deps}} /etc /etc
COPY --from={{base_test_deps}} /env /env

RUN ldconfig

RUN mkdir /exaudfclient /exaudf
COPY /exaudfclient/base /exaudfclient/base

WORKDIR /exaudfclient/base
RUN ["/bin/bash", "-c", "source /env && bash build.sh --config no-tty -c dbg --config python --config slow-wrapper-py3"]
RUN cp -r -L bazel-bin/* /exaudf
RUN ./test_udfclient.sh /exaudf/exaudfclient_py3.sh

WORKDIR /
RUN mkdir /exasol_emulator
COPY emulator/ /exasol_emulator
COPY /exaudfclient/base/exaudflib/zmqcontainer.proto /exasol_emulator
RUN cd /exasol_emulator && protoc zmqcontainer.proto --python_out=.
