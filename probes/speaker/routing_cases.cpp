// SPDX-License-Identifier: MIT
// Tests the actual GPL-3.0-or-later extension header supplied by the build.
#include "speaker_routing.hpp"
#include <cassert>
#include <iostream>
#include <tuple>
#include <vector>

using Policy=pw::SpeakerRouting;
struct Fixture {
  std::vector<std::tuple<uint32_t,std::string,Policy::Value>> writes;
  Policy p{"alsa_output.internal","analog-output-speaker",[this](auto id,const auto& key,const auto& value){
    writes.emplace_back(id,key,value);
  }};
  Fixture() {
    p.ready=true; p.metadata_available=true; p.effects_id=90; p.effects_serial=900;
    p.selected_output=p.default_output=p.device_name;
    p.nodes.emplace(10,Policy::Node{100,p.device_name,false,false,5,0,""});
    p.nodes.emplace(20,Policy::Node{200,"alsa_output.hdmi",false,false,6,0,""});
    p.nodes.emplace(30,Policy::Node{300,"alsa_output.usb",false,false,7,0,""});
    p.routes[{5,0}]="analog-output-speaker"; p.refresh();
  }
  void stream(uint32_t id=1,std::string target="") {
    p.node_changed(id,Policy::Node{1000+id,"player",true,false,UINT32_MAX,-1,target});
  }
  void link(uint32_t sink,uint32_t id=1) {p.links[id]={id,sink};p.refresh();}
  void acknowledge() {
    auto snapshot=writes; writes.clear();
    for(auto& [id,key,value]:snapshot) p.target_changed(id,key,value);
  }
};

int main(int argc,char** argv) {
  assert(argc==2);std::string name=argv[1];Fixture f;
  if(name=="ordinary-speaker") {
    f.stream();f.link(10);assert(f.p.owned.contains(1));assert(f.writes.size()==2);assert(!f.p.bypass());
  } else if(name=="explicit-hdmi-usb") {
    f.stream(1,"alsa_output.hdmi");f.link(20);
    f.stream(2,"300");f.link(30,2);assert(f.p.owned.empty());assert(f.writes.empty());
  } else if(name=="metadata-target-race") {
    f.stream();f.p.target_changed(1,"target.object",Policy::Property{"Spa:Id","200"});
    f.link(10);assert(f.p.owned.empty());assert(f.writes.empty());
  } else if(name=="headphone-bypass-restores") {
    f.stream();f.link(10);f.acknowledge();f.p.routes[{5,0}]="analog-output-headphones";f.p.refresh();
    assert(f.p.bypass());assert(f.p.owned.empty());assert(!f.p.value(1,"target.object"));assert(!f.p.value(1,"target.node"));
  } else if(name=="unknown-route-bypass") {
    f.stream();f.link(10);f.p.routes.clear();f.p.refresh();assert(f.p.bypass());assert(f.p.owned.empty());
  } else if(name=="default-transition") {
    f.stream();f.link(10);f.acknowledge();f.p.default_output="alsa_output.usb";f.p.refresh();
    assert(f.p.owned.empty());assert(f.p.default_output=="alsa_output.usb");
  } else if(name=="explicit-speaker-other-default") {
    f.p.default_output="alsa_output.usb";f.stream(1,f.p.device_name);f.link(10);assert(f.p.owned.contains(1));
  } else if(name=="external-target-wins") {
    f.stream();f.link(10);f.acknowledge();
    f.p.target_changed(1,"target.object",Policy::Property{"Spa:Id","200"});
    assert(f.p.owned.empty());assert(f.p.value(1,"target.object")->value=="200");assert(!f.p.value(1,"target.node"));
  } else if(name=="application-target-change") {
    f.stream();f.link(10);f.acknowledge();auto node=f.p.nodes.at(1);
    node.property_target="alsa_output.usb";f.p.node_changed(1,node);
    assert(f.p.owned.empty());assert(!f.p.value(1,"target.object"));assert(!f.p.value(1,"target.node"));
  } else if(name=="typed-target-restoration") {
    f.stream();f.p.target_changed(1,"target.object",Policy::Property{"Spa:String",f.p.device_name});
    f.link(10);f.acknowledge();f.p.release_all();assert(f.p.value(1,"target.object")==Policy::Value(Policy::Property{"Spa:String",f.p.device_name}));
  } else if(name=="owned-acknowledgments") {
    f.stream();f.link(10);f.p.routes.clear();f.p.refresh();f.acknowledge();
    assert(f.p.owned.empty());assert(!f.p.value(1,"target.object"));assert(f.p.bypass());
  } else if(name=="live-ignored-restores") {
    f.stream();Policy::Value original=Policy::Property{"Spa:String",f.p.device_name};
    f.p.target_changed(1,"target.object",original);f.link(10);f.acknowledge();
    f.p.node_ignored(1);
    assert(f.p.owned.empty());assert(!f.p.nodes.contains(1));
    assert(f.writes.size()==2);
    assert(std::get<1>(f.writes.back())=="target.object");
    assert(std::get<2>(f.writes.back())==original);
  } else if(name=="true-removal-no-restore-write") {
    f.stream();f.link(10);f.acknowledge();f.p.node_removed(1);
    assert(f.writes.empty());assert(f.p.owned.empty());
  } else if(name=="two-route-profile-indices") {
    assert(Policy::route_applies(5,0,5,0));
    assert(!Policy::route_applies(5,0,5,1));
    assert(Policy::route_applies(5,1,5,1));
    assert(!Policy::route_applies(5,1,6,1));
    assert(!Policy::route_applies(5,-1,5,-1));
    f.stream();f.link(10);f.acknowledge();f.p.routes[{5,1}]="hdmi-output-0";f.p.refresh();
    assert(!f.p.bypass());assert(f.p.owned.contains(1));
  } else if(name=="stream-id-reuse") {
    f.stream();f.link(10);f.p.node_removed(1);f.p.node_changed(1,Policy::Node{9999,"new player",true,false,UINT32_MAX,-1,"alsa_output.usb"});
    assert(f.p.owned.empty());assert(!f.p.value(1,"target.object"));
  } else if(name=="sink-removal-resume") {
    f.stream();f.link(10);f.acknowledge();f.p.node_removed(10);assert(f.p.bypass());assert(f.p.owned.empty());
    f.p.node_changed(11,Policy::Node{101,f.p.device_name,false,false,5,0,""});f.link(11);assert(f.p.owned.contains(1));
  } else if(name=="selected-device-and-input") {
    f.stream();f.link(10);f.p.selected_output="alsa_output.hdmi";f.p.refresh();assert(f.p.bypass());assert(f.p.owned.empty());
    f.p.selected_output=f.p.device_name;f.p.node_changed(2,Policy::Node{1002,"recorder",false,false,UINT32_MAX,-1,""});
    f.link(10,2);assert(!f.p.owned.contains(2));
  } else if(name=="blocklist-and-process-all") {
    f.stream();f.link(10);auto node=f.p.nodes.at(1);node.blocked=true;f.p.node_changed(1,node);assert(f.p.owned.empty());
    node.blocked=false;f.p.process_outputs=false;f.p.node_changed(1,node);assert(f.p.owned.empty());
  } else if(name=="startup-barrier") {
    f.p.ready=false;f.stream();f.link(10);assert(f.p.bypass());assert(f.p.owned.empty());
    f.p.ready=true;f.p.refresh();assert(f.p.owned.contains(1));
  } else if(name=="partial-scope-and-stock") {
    Policy partial{f.p.device_name,"",[](auto,const auto&,const auto&){assert(false);}};
    partial.ready=partial.metadata_available=true;partial.refresh();assert(partial.bypass());
    Policy stock{"","",[](auto,const auto&,const auto&){assert(false);}};assert(!stock.bypass());
  } else {std::cerr<<"Unknown case\n";return 2;}
  std::cout<<name<<" passed\n";
}
