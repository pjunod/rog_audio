// SPDX-License-Identifier: MIT
// Exercise the actual source-bound output-route cache; no PipeWire session.
#include "output_route_cache.hpp"
#include <stdexcept>
#include <string>
#include <cstdint>
#include <iostream>

struct Node {
  uint32_t id=8;
  uint64_t serial=100;
  uint32_t device_id=3;
  int profile_device=0;
  std::string device_route_name,device_route_description;
};
using Cache=pw::OutputRouteCache<std::string>;
void require(bool value) {if(!value)throw std::runtime_error("route-state assertion failed");}
void run(const std::string& name) {
  Cache cache;Node node;
  if(name=="route-before-node" || name=="node-before-route" || name=="node-return") {
    if(name=="node-before-route")require(!cache.apply(node));
    cache.remember(3,0,"analog-output-speaker","Speakers");
    require(cache.apply(node));require(node.device_route_description=="Speakers");
    if(name=="node-return") {
      node=Node{};node.id=19;node.serial=200;
      require(cache.apply(node));require(node.device_route_description=="Speakers");
    }
  } else if(name=="profile-isolation") {
    cache.remember(3,0,"analog-output-speaker","Speakers");
    cache.remember(3,1,"hdmi-output-0","HDMI");node.profile_device=1;
    require(cache.apply(node));require(node.device_route_description=="HDMI");
    node.profile_device=0;require(cache.apply(node));require(node.device_route_description=="Speakers");
  } else if(name=="invalidation") {
    const auto token=cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    cache.invalidate(3);require(cache.apply(node));
    require(node.device_route_description.empty());require(!cache.current(3,0,token));
  } else if(name=="stale-route") {
    const auto old=cache.remember(3,0,"speaker","Speakers");
    const auto now=cache.remember(3,0,"headphones","Headphones");
    require(!cache.current(3,0,old));require(cache.current(3,0,now));
    cache.apply(node);require(node.device_route_description=="Headphones");
  } else if(name=="device-id-reuse") {
    const auto old=cache.remember(3,0,"speaker","Speakers");cache.invalidate(3);
    const auto now=cache.remember(3,0,"headphones","Headphones");
    require(old!=now && !cache.current(3,0,old));cache.apply(node);
    require(node.device_route_description=="Headphones");
  } else if(name=="missing-profile") {
    require(cache.remember(3,-1,"speaker","Speakers")==0);
    cache.remember(3,0,"speaker","Speakers");node.profile_device=-1;
    require(!cache.apply(node));require(node.device_route_description.empty());
  } else if(name=="binding-change") {
    cache.remember(3,0,"speaker","Speakers");cache.apply(node);node.device_id=4;
    require(cache.apply(node));require(node.device_route_description.empty());
  } else if(name=="volume-update") {
    cache.remember(3,0,"speaker","Speakers");require(cache.apply(node));
    require(!cache.apply(node));require(!cache.apply(node));
  } else if(name=="queued-node-removal") {
    Node gone;gone.id=UINT32_MAX;gone.serial=UINT32_MAX;
    require(!Cache::same_instance(node,gone));require(!Cache::same_instance(gone,gone));
  } else if(name=="queued-node-reuse") {
    Node replacement=node;replacement.serial++;
    require(!Cache::same_instance(node,replacement));require(Cache::same_instance(node,node));
  } else if(name=="duplicate-route-notification" || name=="invalidation-same-route") {
    cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    require(cache.changed_since_notification(node));cache.notified(node);
    if(name=="invalidation-same-route") {cache.invalidate(3);cache.apply(node);}
    cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    require(!cache.changed_since_notification(node));
  } else if(name=="pending-invalidation-same-route") {
    const auto old=cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    require(cache.changed_since_notification(node)); // Scheduled, not notified.
    cache.invalidate(3);
    const auto current=cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    require(!cache.current(3,0,old) && cache.current(3,0,current));
    require(cache.changed_since_notification(node));cache.notified(node);
    require(!cache.changed_since_notification(node));
  } else if(name=="notification-removal") {
    cache.remember(3,0,"speaker","Speakers");cache.apply(node);cache.notified(node);
    cache.remove_device(3);cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    require(cache.changed_since_notification(node));cache.notified(node);
    cache.remove_node(node.id,node.serial);require(cache.changed_since_notification(node));
  } else if(name=="description-change") {
    cache.remember(3,0,"speaker","Speakers");cache.apply(node);
    cache.remember(3,0,"speaker","Haut-parleurs");require(cache.apply(node));
    require(node.device_route_description=="Haut-parleurs");
  } else throw std::runtime_error("unknown case");
}
int main(int argc,char** argv) {
  try {if(argc!=2)return 2;run(argv[1]);return 0;}
  catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
