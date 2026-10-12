// SPDX-License-Identifier: MIT
// Synthetic PipeWire Device with a real Route parameter; no ALSA/device access.
#include <pipewire/pipewire.h>
#include <pipewire/device.h>
#include <spa/param/route.h>
#include <spa/pod/builder.h>
#include <spa/utils/hook.h>
#include <iostream>
#include <string>
#include <unistd.h>

struct Device {
  spa_interface interface{};
  spa_hook_list listeners{};
  pw_properties* props=nullptr;
  spa_param_info parameter{SPA_PARAM_Route,SPA_PARAM_INFO_READ | SPA_PARAM_INFO_WRITE};
  pw_device_info info{};
  std::string route="analog-output-speaker",description="Speakers";
  pw_main_loop* loop=nullptr;
  static int add(void* object,spa_hook* hook,const pw_device_events* events,void* data) {
    auto* d=static_cast<Device*>(object);
    spa_hook_list_append(&d->listeners,hook,events,data);
    if(events->info)events->info(data,&d->info);
    return 0;
  }
  static int subscribe(void*,uint32_t*,uint32_t) {return 0;}
  static int enumerate(void* object,int seq,uint32_t id,uint32_t start,uint32_t count,const spa_pod*) {
    auto* d=static_cast<Device*>(object);
    if(id!=SPA_PARAM_Route || start!=0 || count==0)return 0;
    uint8_t buffer[1024];spa_pod_builder builder=SPA_POD_BUILDER_INIT(buffer,sizeof(buffer));
    auto* pod=static_cast<spa_pod*>(spa_pod_builder_add_object(&builder,
      SPA_TYPE_OBJECT_ParamRoute,SPA_PARAM_Route,
      SPA_PARAM_ROUTE_index,SPA_POD_Int(0),SPA_PARAM_ROUTE_device,SPA_POD_Int(0),
      SPA_PARAM_ROUTE_direction,SPA_POD_Id(SPA_DIRECTION_OUTPUT),
      SPA_PARAM_ROUTE_name,SPA_POD_String(d->route.c_str()),
      SPA_PARAM_ROUTE_description,SPA_POD_String(d->description.c_str()),
      SPA_PARAM_ROUTE_available,SPA_POD_Id(SPA_PARAM_AVAILABILITY_yes)));
    spa_hook_list_call(&d->listeners,pw_device_events,param,0,seq,id,0,1,pod);
    return 0;
  }
  static int set(void*,uint32_t,uint32_t,const spa_pod*) {return -ENOTSUP;}
  void changed(const std::string& command) {
    if(command=="speaker") {route="analog-output-speaker";description="Speakers";}
    else if(command=="headphones") {route="analog-output-headphones";description="Headphones";}
    else {route="unknown-route";description="Unknown";}
    parameter.flags^=SPA_PARAM_INFO_SERIAL;
    info.change_mask=PW_DEVICE_CHANGE_MASK_PARAMS;
    spa_hook_list_call(&listeners,pw_device_events,info,0,&info);
    std::cout<<"route "<<command<<std::endl;
  }
};
const pw_device_methods methods={.version=PW_VERSION_DEVICE_METHODS,.add_listener=Device::add,
 .subscribe_params=Device::subscribe,.enum_params=Device::enumerate,.set_param=Device::set};
static void input(void* object,int,uint32_t) {
  auto* d=static_cast<Device*>(object);std::string command;
  if(!std::getline(std::cin,command)) {pw_main_loop_quit(d->loop);return;}
  d->changed(command);
}
static void bound(void*,uint32_t id) {std::cout<<"device "<<id<<std::endl;}
int main() {
  pw_init(nullptr,nullptr);Device d;spa_hook_list_init(&d.listeners);
  d.interface=SPA_INTERFACE_INIT(PW_TYPE_INTERFACE_Device,PW_VERSION_DEVICE,&methods,&d);
  d.props=pw_properties_new("device.name","rog-synthetic-device","device.api","rog-synthetic",
    "device.description","Synthetic speaker route device","media.class","Audio/Device",nullptr);
  d.info={.id=0,.change_mask=PW_DEVICE_CHANGE_MASK_ALL,.props=&d.props->dict,.params=&d.parameter,.n_params=1};
  d.loop=pw_main_loop_new(nullptr);
  auto* context=pw_context_new(pw_main_loop_get_loop(d.loop),nullptr,0);
  auto* core=pw_context_connect(context,nullptr,0);
  if(!core)return 2;
  auto* proxy=pw_core_export(core,PW_TYPE_INTERFACE_Device,&d.props->dict,&d.interface,0);
  if(!proxy)return 3;
  spa_hook listener{};pw_proxy_events events{};events.version=PW_VERSION_PROXY_EVENTS;events.bound=bound;
  pw_proxy_add_listener(proxy,&listener,&events,nullptr);
  pw_loop_add_io(pw_main_loop_get_loop(d.loop),STDIN_FILENO,SPA_IO_IN,false,input,&d);
  pw_main_loop_run(d.loop);
  spa_hook_remove(&listener);pw_proxy_destroy(proxy);pw_core_disconnect(core);
  pw_context_destroy(context);pw_main_loop_destroy(d.loop);pw_properties_free(d.props);pw_deinit();
}
