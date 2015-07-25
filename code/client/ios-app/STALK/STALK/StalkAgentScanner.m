//
//  StalkAgentScanner.m
//  STALK
//
//  Created by emerson on 2015. 7. 24..
//  Copyright (c) 2015년 emerson. All rights reserved.
//

#include <arpa/inet.h>
#import "GCDAsyncUdpSocket.h"
#import "StalkAgentScanner.h"


static const int BROADCAST_PORT = 8988;
static NSString *PREFIX = @"STALKAGENT@";

@implementation StalkAgent

@end


@interface StalkAgentScanner() <GCDAsyncUdpSocketDelegate>
{
    NSMutableArray *__agents;
    NSMutableDictionary *__host_to_agents;
    void (^__callback)();
    GCDAsyncUdpSocket *__socket;
}

@end


@implementation StalkAgentScanner

- (id)init
{
    self = [super init];
    __agents = [NSMutableArray new];
    __host_to_agents = [NSMutableDictionary new];

    __socket = [[GCDAsyncUdpSocket alloc]initWithDelegate:self delegateQueue:dispatch_get_main_queue()];

    NSError *error;
    [__socket bindToPort:BROADCAST_PORT error:&error];
    NSAssert(error == nil, @"");

    [__socket beginReceiving:&error];
    NSAssert(error == nil, @"");

    //
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        while(YES) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [self garbageCollect];
            });
            [NSThread sleepForTimeInterval:10.0];
        }
    });

    return self;
}

- (NSArray *)agents
{
    return __agents;
}

- (void)setChangingHandler:(void (^)())callback
{
    __callback = callback;
}

- (void)garbageCollect
{
    double cut = [NSDate date].timeIntervalSince1970 - 10.0;

    NSMutableArray *names = nil;
    NSMutableArray *agents = nil;

    for(NSString *host_name in __host_to_agents) {
        StalkAgent *agent = __host_to_agents[host_name];
        if (agent.update_time.timeIntervalSince1970 < cut) {
            if (!names) {
                names = [NSMutableArray new];
            }

            [names addObject:host_name];

            if (!agents) {
                agents = [NSMutableArray new];
            }

            [agents addObject:agent];
        }
    }

    //
    for(NSString *host_name in names) {
        [__host_to_agents removeObjectForKey:host_name];
    }
    for(StalkAgent *agent in agents) {
        [__agents removeObject:agent];
    }

    if (names.count) {
        if (__callback) {
            __callback();
        }
    }
}

- (void)udpSocket:(GCDAsyncUdpSocket *)sock didReceiveData:(NSData *)data
      fromAddress:(NSData *)address
withFilterContext:(id)filterContext
{
    NSString *s = [[NSString alloc]initWithData:data encoding:NSUTF8StringEncoding];

    //STALKAGENT@emersonMBP.local
    //WEB_UI:8900
    //WEB_SSH:8022
    if ([s hasPrefix:PREFIX]) {
        // sender address
        struct sockaddr_in *fromAddressV4 = (struct sockaddr_in *)address.bytes;
        char *fromIPAddress = inet_ntoa(fromAddressV4->sin_addr);
        NSString *ip_address = [[NSString alloc] initWithUTF8String:fromIPAddress];

        // parse message
        BOOL dirty = NO;
        NSString *host_name = nil;
        int web_ui_port = 0;
        int web_ssh_port = 0;

        NSArray *lines = [s componentsSeparatedByString:@"\n"];

        // first line
        s = lines[0];
        if (s) {
            int index = (int)(PREFIX.length);
            host_name = [s substringFromIndex:index];
        }

        // remaining lines
        for (int i = 1; i < lines.count; ++i) {
            NSString *s = lines[i];
            if ([s hasPrefix:@"WEB_UI:"]) {
                int index = (int)(@"WEB_UI:".length);
                web_ui_port = [[s substringFromIndex:index] intValue];
            }
            else if ([s hasPrefix:@"WEB_SSH:"]) {
                int index = (int)(@"WEB_SSH:".length);
                web_ssh_port = [[s substringFromIndex:index] intValue];
            }
        }

        StalkAgent *agent = __host_to_agents[host_name];
        if (agent) {
            if (agent.web_ui_port != web_ui_port) {
                agent.web_ui_port = web_ui_port;
                agent.update_time = [NSDate date];
                dirty = YES;
            }

            if (agent.web_ssh_port != web_ssh_port) {
                agent.web_ssh_port = web_ssh_port;
                agent.update_time = [NSDate date];
                dirty = YES;
            }

            if (![agent.ip_address isEqualToString:ip_address]) {
                agent.ip_address = ip_address;
                agent.update_time = [NSDate date];
                dirty = YES;
            }
        }
        else {
            agent = [StalkAgent new];
            agent.host_name = host_name;
            agent.web_ui_port = web_ui_port;
            agent.web_ssh_port = web_ssh_port;
            agent.ip_address = ip_address;
            agent.update_time = [NSDate date];
            __host_to_agents[host_name] = agent;
            [__agents addObject:agent];

            dirty = YES;
        }

        //
        if (dirty && __callback) {
            __callback();
        }
    }

}

@end
