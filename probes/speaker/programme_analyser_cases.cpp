// SPDX-License-Identifier: MIT
// Deterministic threaded ownership cases on the actual native state header.
#include "programme_analyser_state.hpp"
#include <array>
#include <atomic>
#include <chrono>
#include <future>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>

using namespace std::chrono_literals;
struct State {
  int id;
  int history=0;
  static inline std::array<std::atomic<int>, 4> alive{};
  static inline std::array<std::atomic<int>, 4> destroyed{};
  explicit State(int value):id(value) { alive[id]++; }
};
struct Delete {
  void operator()(State* state) const {
    if (!state) return;
    State::alive[state->id]--; State::destroyed[state->id]++;
    delete state;
  }
};
using Slot=programme_loudness::AnalyserState<State, Delete>;
void require(bool value) {
  if (!value) throw std::runtime_error("analyser ownership assertion failed");
}
bool configure(State* state, int history) {
  require(state && State::alive[state->id]==1);
  state->history=history; return true;
}
void wait(std::future<void>& future) {
  require(future.wait_for(5s)==std::future_status::ready); future.get();
}
void initialize(Slot& slot) {
  auto request=slot.request(48000);
  require(slot.replace(request, [](unsigned int rate) {
    require(rate==48000); return new State(1);
  }, configure));
}
void run(const std::string& name) {
  Slot slot; initialize(slot);
  if (name=="history-during-reconstruction") {
    auto request=slot.request(48000);
    std::promise<void> entered, release;
    auto started=entered.get_future(); auto resume=release.get_future().share();
    auto worker=std::async(std::launch::async, [&] {
      require(slot.replace(request, [&](unsigned int) {
        entered.set_value(); require(resume.wait_for(5s)==std::future_status::ready);
        return new State(2);
      }, configure));
    });
    wait(started); require(slot.set_history(42, configure));
    require(State::alive[1]==1); release.set_value(); wait(worker);
    slot.with_state([](State* state) {require(state && state->id==2 && state->history==42);});
    require(State::destroyed[1]==1);
  } else if (name=="stale-generation-refused") {
    auto old=slot.request(48000);
    std::promise<void> entered, release;
    auto started=entered.get_future(); auto resume=release.get_future().share();
    auto worker=std::async(std::launch::async, [&] {
      require(!slot.replace(old, [&](unsigned int) {
        entered.set_value(); require(resume.wait_for(5s)==std::future_status::ready);
        return new State(2);
      }, configure));
    });
    wait(started); auto current=slot.request(96000);
    require(slot.replace(current, [](unsigned int rate) {
      require(rate==96000); return new State(3);
    }, configure));
    release.set_value(); wait(worker);
    require(slot.ready_for(96000) && !slot.ready_for(48000));
    slot.with_state([](State* state) {require(state && state->id==3);});
    require(State::destroyed[2]==1 && State::alive[3]==1);
  } else if (name=="processing-lease-serializes-history-and-swap") {
    std::promise<void> entered, release, allocated, configure_entered;
    auto started=entered.get_future(); auto resume=release.get_future().share();
    auto built=allocated.get_future(); auto configured=configure_entered.get_future();
    auto processing=std::async(std::launch::async, [&] {
      slot.with_state([&](State* state) {
        require(state && state->id==1); entered.set_value();
        require(resume.wait_for(5s)==std::future_status::ready);
        require(State::alive[1]==1 && State::destroyed[1]==0);
      });
    });
    wait(started);
    // Request itself must wait for the current borrowed state to be released.
    auto replacing=std::async(std::launch::async, [&] {
      auto request=slot.request(48000);
      require(slot.replace(request, [&](unsigned int) {
        allocated.set_value(); return new State(2);
      }, configure));
    });
    auto history=std::async(std::launch::async, [&] {
      require(slot.set_history(42, [&](State* state, int seconds) {
        configure_entered.set_value(); return configure(state, seconds);
      }));
    });
    require(built.wait_for(50ms)==std::future_status::timeout);
    require(configured.wait_for(50ms)==std::future_status::timeout);
    release.set_value(); wait(processing); wait(replacing); wait(history);
    slot.with_state([](State* state) {require(state && state->id==2 && state->history==42);});
    require(State::destroyed[1]==1);
  } else if (name=="failed-candidate-never-ready") {
    auto request=slot.request(48000);
    require(!slot.replace(request, [](unsigned int)->State* {return nullptr;}, configure));
    require(!slot.ready_for(48000));
    slot.with_state([](State* state) {require(state==nullptr);});
    require(State::alive[1]==1);
    request=slot.request(48000);
    require(!slot.replace(request, [](unsigned int) {return new State(2);},
                         [](State*, int) {return false;}));
    require(!slot.ready_for(48000) && State::destroyed[2]==1);
    slot.invalidate(); slot.clear();
    require(State::destroyed[1]==1);
  } else throw std::runtime_error("unknown case");
  slot.clear();
  for (auto& count:State::alive) require(count==0);
}
int main(int argc, char** argv) {
  try {if(argc!=2)return 2;run(argv[1]);return 0;}
  catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
