//
//  WebScreen.m
//  STALK
//
//  Created by emerson on 2015. 7. 25..
//  Copyright (c) 2015년 emerson. All rights reserved.
//

#import "WebScreen.h"

@interface WebScreen ()<UIWebViewDelegate>

@property (nonatomic) IBOutlet UIWebView *webView;

@end

@implementation WebScreen

- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
    [self.webView loadRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:self.address]]];
}

- (BOOL)webView:(UIWebView *)webView shouldStartLoadWithRequest:(NSURLRequest *)request navigationType:(UIWebViewNavigationType)navigationType
{
    return YES;
}

@end
