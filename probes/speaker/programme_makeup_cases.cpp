// SPDX-License-Identifier: MIT
// Actual pinned native gain controller; no audio/session/device access.
#include "programme_makeup_gain.hpp"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

void require(bool value) {
  if (!value) throw std::runtime_error("programme makeup assertion failed");
}
void near(double actual, double expected) {
  require(std::isfinite(actual) && std::abs(actual - expected) < 1e-10);
}
void run(const std::string& name) {
  programme_loudness::MakeupGain gain;
  const double cap = std::pow(10.0, 6.0 / 20.0);
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();
  if (name == "requested-cap") {
    near(gain.update(100, 6, 0, 0, true), cap);
    near(gain.update(100, 0, 0, 0, true), 1);
    near(gain.update(100, 36, 0, 0, true), std::pow(10.0, 36.0/20.0));
  } else if (name == "retained-cap-reduction") {
    near(gain.update(100, 36, 0, 0, true), std::pow(10.0, 36.0/20.0));
    near(gain.update(100, 6, .999, .999, true), cap);
    near(gain.update(100, 0, .999, .999, true), 1);
  } else if (name == "silence-reset") {
    gain.update(100, 6, 0, 0, true);
    near(gain.update(100, 6, .9, .9, false), 1);
    near(gain.value(), 1);
    near(gain.update(100, 6, .9, .9, true), .9 + .1*cap);
  } else if (name == "invalid-request-reset") {
    for (double bad : {nan, inf, -inf, -1.0}) {
      gain.update(100, 6, 0, 0, true);
      near(gain.update(bad, 6, .9, .9, true), 1);
    }
  } else if (name == "invalid-cap-and-smoothing") {
    for (double bad : {nan, inf, -inf}) {
      gain.update(100, 36, 0, 0, true);
      near(gain.update(100, bad, .9, .9, true), 1);
      gain.update(100, 6, 0, 0, true);
      near(gain.update(100, 6, bad, .9, true), 1);
      gain.update(100, 6, 0, 0, true);
      near(gain.update(100, 6, .9, bad, true), 1);
    }
  } else if (name == "louder-source-reduces") {
    near(gain.update(100, 6, 0, 0, true), cap);
    const double next = gain.update(.5, 6, .5, .9, true);
    near(next, .5*cap + .5*.5);
    require(next < cap);
    near(gain.update(.5, 6, 0, .9, true), .5);
  } else if (name == "smoothing-no-overshoot") {
    near(gain.update(100, 6, .1, .75, true), .75 + .25*cap);
    for (int i=0; i<100; ++i) {
      double previous=gain.value();
      double next=gain.update(100, 6, .1, .75, true);
      require(next >= previous && next <= cap);
    }
    for (int i=0; i<100; ++i) {
      double previous=gain.value();
      double next=gain.update(.1, 6, .25, .75, true);
      require(next <= previous && next >= .1);
    }
  } else if (name == "zero-request-and-reset") {
    near(gain.update(0, 6, 0, 0, true), 0);
    gain.reset(); near(gain.value(), 1);
    // Out-of-range control coefficients cannot extrapolate gain.
    near(gain.update(100, 6, -5, -5, true), cap);
    near(gain.update(.5, 6, 5, 5, true), cap);
  } else throw std::runtime_error("unknown case");
}
int main(int argc, char** argv) {
  try { if (argc != 2) return 2; run(argv[1]); return 0; }
  catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
