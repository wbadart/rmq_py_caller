rmq_py_caller lets you put any valid Python program in `PY_SETUP`. This is very
helpful for injecting debugging, simple analytics, data transformations, and
more into large scale Docker service architectures. For example:

```yaml
version: "3.4"
services:
    # Lots of interesting production services
    # ...
    
    my_simple_program:
      image: wbadart/rmq_py_caller
      environment:
        PY_SETUP: |
          import logging
          import ipaddress

          def processor(src_net, dst_net):
              logging.info("Got %s and %s", src_net, dst_net)
              src_net, dst_net = map(ipaddress.ip_network, (src_net, dst_net))
              return dst_net.subnet_of(src_net)
          
        PY_TARGET: "processor"
        ARG_ADAPTER: >-
          [ .net.src.mask, .net.dst.mask ]
        OUTPUT_ADAPTER: >-
          .orig * {
            dst_subnet_of_src: .result
          }
        INPUT_QUEUE: "data_in"
        OUTPUT_EXCHANGE: "data_out"
        RABTAP_AMQPURI: "amqp://guest:guest@rabbitmq-hostname:5672/"
```

This example takes an object with two network masks, and adds a field
(`dst_subnet_of_src`) which records if one is a subnetwork of the other.
