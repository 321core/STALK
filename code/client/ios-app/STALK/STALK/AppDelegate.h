//
//  AppDelegate.h
//  STALK
//
//  Created by emerson on 2015. 7. 24..
//  Copyright (c) 2015년 emerson. All rights reserved.
//

#import <UIKit/UIKit.h>
#import "StalkAgentScanner.h"

@interface AppDelegate : UIResponder <UIApplicationDelegate>

@property (strong, nonatomic) UIWindow *window;
@property (nonatomic) StalkAgentScanner *scanner;

@end


static inline AppDelegate* get_app_delegate()
{
    return (AppDelegate *)[[UIApplication sharedApplication] delegate];
}
