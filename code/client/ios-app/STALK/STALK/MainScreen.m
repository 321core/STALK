//
//  ViewController.m
//  STALK
//
//  Created by emerson on 2015. 7. 24..
//  Copyright (c) 2015년 emerson. All rights reserved.
//

#import "MainScreen.h"
#import "AppDelegate.h"
#import "WebScreen.h"

@interface MainScreen ()
{
    NSArray *__agents;
}
@end

@implementation MainScreen

- (void)reloadData
{
    __agents = [get_app_delegate().scanner.agents copy];
    [self.tableView reloadData];
}

- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
    [self reloadData];
    [get_app_delegate().scanner setChangingHandler:^{
        [self reloadData];
    }];
}

- (void)viewDidDisappear:(BOOL)animated
{
    [super viewDidDisappear:animated];
    [get_app_delegate().scanner setChangingHandler:nil];
}

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section
{
    return __agents.count;
}

- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath
{
    UITableViewCell *cell = [tableView dequeueReusableCellWithIdentifier:@"CELL"];

    StalkAgent *agent = [__agents objectAtIndex:indexPath.row];
    cell.textLabel.text = agent.host_name;
    cell.detailTextLabel.text = [NSString stringWithFormat:@"%@:%d", agent.ip_address, agent.web_port];
    
    return cell;
}

- (void)prepareForSegue:(UIStoryboardSegue *)segue sender:(id)sender
{
    WebScreen *ws = (WebScreen *)segue.destinationViewController;
    StalkAgent *agent = get_app_delegate().scanner.agents[self.tableView.indexPathForSelectedRow.row];
    ws.address = [NSString stringWithFormat:@"http://%@:%d", agent.ip_address, agent.web_port];
}

@end
