FROM wbadart/rmq_pyctx_caller

WORKDIR /src
COPY . .
RUN pip install .

ENV CTX_MODULE "my_analytic"
ENV CTX_NAME "do_analytic"

ENV ARG_ADAPTER "{field: . | to_entries | .[0].value}"
ENV OUTPUT_ADAPTER "{len: .result, id: .orig.id}"
