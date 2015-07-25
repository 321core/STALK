//
//  StalkAgentScanner.h
//  STALK
//
//  Created by emerson on 2015. 7. 24..
//  Copyright (c) 2015년 emerson. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface StalkAgent : NSObject
@property NSString *host_name;
@property NSString *ip_address;
@property int web_port;
@property NSDate *update_time;
@end


@interface StalkAgentScanner : NSObject

@property (readonly) NSArray *agents;

- (void)setChangingHandler:(void(^)())callback;

@end
