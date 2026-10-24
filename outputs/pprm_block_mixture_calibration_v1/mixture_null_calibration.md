# PPI block e-process null stress calibration

This Monte Carlo stress test used 2000 independent streams per cell and 240 completed blocks per stream. Each block estimate was drawn i.i.d. from the two endpoints of the declared support, with the upper-endpoint probability chosen to give the listed conditional mean. It tests the sharp boundary and a null 0.02 below it. The experiment checks implementation-level false-escalation behavior; it does not prove the e-process theorem or cover serially dependent block estimates.

|Null|Conditional mean|Method|Streams|False escalations|Rate|Wilson 95% interval|
|---|---:|---|---:|---:|---:|---:|
|boundary|0.510|CM-EB|2000|0|0.0000|[0.0000, 0.0019]|
|boundary|0.510|positive_betting|2000|73|0.0365|[0.0291, 0.0456]|
|boundary|0.510|mixture_w=0.1|2000|65|0.0325|[0.0256, 0.0412]|
|boundary|0.510|mixture_w=0.25|2000|50|0.0250|[0.0190, 0.0328]|
|boundary|0.510|mixture_w=0.5|2000|29|0.0145|[0.0101, 0.0207]|
|boundary|0.510|mixture_w=0.75|2000|13|0.0065|[0.0038, 0.0111]|
|boundary|0.510|mixture_w=0.9|2000|7|0.0035|[0.0017, 0.0072]|
|below_boundary|0.490|CM-EB|2000|0|0.0000|[0.0000, 0.0019]|
|below_boundary|0.490|positive_betting|2000|35|0.0175|[0.0126, 0.0242]|
|below_boundary|0.490|mixture_w=0.1|2000|30|0.0150|[0.0105, 0.0213]|
|below_boundary|0.490|mixture_w=0.25|2000|25|0.0125|[0.0085, 0.0184]|
|below_boundary|0.490|mixture_w=0.5|2000|15|0.0075|[0.0046, 0.0123]|
|below_boundary|0.490|mixture_w=0.75|2000|6|0.0030|[0.0014, 0.0065]|
|below_boundary|0.490|mixture_w=0.9|2000|2|0.0010|[0.0003, 0.0036]|

Development-only calibration; power is not evaluated here.
