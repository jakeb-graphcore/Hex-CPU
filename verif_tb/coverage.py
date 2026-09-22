from itertools import product
import tb_config
import os

class Coverpoint:
    def __init__(self, name, bucket_size=1):
        self.name = name
        self.axis_map = {}
        self.buckets = {}
        self.bucket_size = bucket_size

    def add_axis(self, name, values):
        assert name not in self.axis_map, f"Axis `{name}` has already been added to coverpoint {self.name}"
        for val in values:
            assert isinstance(val, int) or isinstance(val, str), "Values of an axis must be an integer or a string"
            if isinstance(val, str):
                illegal_chars = ["'", ":", ","]
                for char in illegal_chars:
                    assert char not in val, f"{char} is an illegal character in {val!r}"
        self.axis_map[name] = tuple(values)

    def gen_buckets(self):
        all_values = [axis_values for axis_values in self.axis_map.values()]
        self.buckets = {bucket: 0 for bucket in product(*all_values)}

    def incr(self, bucket, value=1):
        assert bucket in self.buckets, f"{bucket!r} is not a valid bucket."
        self.buckets[bucket] += value

    def reset(self):
        for bucket in self.buckets:
            self.buckets[bucket] = 0


class Covergroup:
    def __init__(self):
        self.coverpoints = {}

    def __getitem__(self, name):
        assert name in self.coverpoints, f"`{name}` is not a coverpoint."
        return self.coverpoints[name]

    def add_coverpoint(self, name):
        assert name not in self.coverpoints, f"`{name}` is already a coverpoint."
        self.coverpoints[name] = Coverpoint(name)

    def gen_buckets(self):
        for cp in self.coverpoints.values():
            cp.gen_buckets()

    def sub_report(self, seed):
        sub_report_loc = os.path.join(tb_config.LOG_ROOT, f"sub_coverage_0x{seed:08x}.log")
        with open(sub_report_loc, "w") as file:
            for cp in self.coverpoints.values():
                for bucket, count in cp.buckets.items():
                    file.write(f"{cp.name}:{bucket}:{count}\n")

    def parse_bucket(self, bucket_str):
        bucket_str = bucket_str.removeprefix("(").removesuffix(")")
        bucket = []
        for val in bucket_str.split(","):
            val = val.strip()
            if val == "":
                break
            if val.startswith("'"):
                bucket.append(val.removeprefix("'").removesuffix("'"))
            else:
                bucket.append(int(val))
        return tuple(bucket)

    def collect_sub_reports(self):
        for filename in os.listdir(tb_config.LOG_ROOT):
            if filename.startswith("sub_coverage"):
                with open(os.path.join(tb_config.LOG_ROOT, filename), "r") as file:
                    for line in file.readlines():
                        name, bucket, count = line.split(":")
                        self.coverpoints[name].incr(self.parse_bucket(bucket), int(count))

    def report(self):
        for cp in self.coverpoints.values():
            cp.reset()
        self.collect_sub_reports()
        report_loc=os.path.join(tb_config.LOG_ROOT, "coverage.log")
        total_buckets_hit = 0
        total_buckets = 0
        with open(report_loc, "w") as file:
            file.write("--------------------COVERAGE REPORT--------------------\n\n")
            for cp in self.coverpoints.values():
                file.write(f"\n----------{cp.name}----------\n")
                file.write(f"{tuple(cp.axis_map)}\n")
                for bucket, count in cp.buckets.items():
                    total_buckets_hit += min(count, cp.bucket_size)
                    total_buckets += cp.bucket_size
                    file.write(f"{bucket}: {count}\n")
        with open(os.path.join(tb_config.LOG_ROOT, "coverage_results.log"), "w") as file:
            file.write(f"Total buckets hit: {total_buckets_hit}\n")
            file.write(f"Total buckets: {total_buckets}\n")
            file.write(f"Coverage: {(total_buckets_hit / total_buckets) * 100}%\n")
