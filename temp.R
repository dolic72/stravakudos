by.month <- d %>% 
  count(monat, fullname)

ggplot(by.month, aes(x = fullname, y = n, fill = myorange)) + 
  geom_bar(stat='identity') +
  theme_bw() +
  coord_flip() + 
  transition_states(
    monat,
    transition_length = 2,
    state_length = 1) +
  ease_aes('sine-in-out')




by.month.fmt <- by.month %>%
  group_by(monat) %>%
  # The * 1 makes it possible to have non-integer ranks while sliding
  mutate(rank = rank(-n),
         Value_rel = n/n[rank == 1],
         Value_lbl = paste0(n)) %>%
  group_by(fullname) %>% 
  filter(rank <= 10) %>%
  ungroup()

staticplot = ggplot(by.month, aes(rank, group = country_name, 
                                  fill = as.factor(country_name), color = as.factor(country_name))) +
  geom_tile(aes(y = value/2,
                height = value,
                width = 0.9), alpha = 0.8, color = NA) +
  geom_text(aes(y = 0, label = paste(country_name, " ")), vjust = 0.2, hjust = 1) +
  geom_text(aes(y=value,label = Value_lbl, hjust=0)) +
  coord_flip(clip = "off", expand = FALSE) +
  scale_y_continuous(labels = scales::comma) +
  scale_x_reverse() +
  guides(color = FALSE, fill = FALSE) +
  theme(axis.line=element_blank(),
        axis.text.x=element_blank(),
        axis.text.y=element_blank(),
        axis.ticks=element_blank(),
        axis.title.x=element_blank(),
        axis.title.y=element_blank(),
        legend.position="none",
        panel.background=element_blank(),
        panel.border=element_blank(),
        panel.grid.major=element_blank(),
        panel.grid.minor=element_blank(),
        panel.grid.major.x = element_line( size=.1, color="grey" ),
        panel.grid.minor.x = element_line( size=.1, color="grey" ),
        plot.title=element_text(size=25, hjust=0.5, face="bold", colour="grey", vjust=-1),
        plot.subtitle=element_text(size=18, hjust=0.5, face="italic", color="grey"),
        plot.caption =element_text(size=8, hjust=0.5, face="italic", color="grey"),
        plot.background=element_blank(),
        plot.margin = margin(2,2, 2, 4, "cm"))
