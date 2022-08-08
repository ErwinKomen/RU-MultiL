
myRcode <- function(number, bericht) {
  list(newvalue = number * 2, bericht = bericht, status = "alles goed")
}


# FUnction that assumes we are receiving the whole JSON data 
forestPrepare <- function(dataset) {
  # Make sure the $Dataset part is read as a TIBBLE
  dat <- dataset %>% as.tibble
   
  # Aanpassingen dataset o.b.v. welke predictor geselecteerd is
  
  # De volgende code moet ALTIJD gerund worden voor model1 (zie volgende sectie). 
  # Daarnaast moet de dataset die uit deze code komt OOK gebruikt worden voor model2 
  # als één van de volgende predictors geselecteerd is: 
  #    target_language, task_type, task_detailed, linguistic_property, surface_overlap_author, target_or_child_system.
  dat1 <- dat %>%
    group_by(short_cite, task_number, linguistic_property, linguistic_property_detailed, monolingual_group,
             # onderstaande rij variabelen zouden als het goed is altijd hetzelfde moeten zijn als we op bovenstaande variabelen gegroepeerd hebben -- heb ze hier alleen toegevoegd om te zorgen dat ze in de nieuwe dataset belanden
             data_collection, target_language, other_language, task_type, task_detailed, surface_overlap_author, target_or_child_system, predicted_direction_difference_2L1, SD_L1, n_L1, CLI_predicted) %>%
    # compute pooled means and standard deviations
    mutate(mean_2L1 = n_2L1/sum(n_2L1) * mean_2L1,
           mean_L1 = n_L1/sum(n_L1) * mean_L1,
           SD_2L1 = ((n_2L1 - 1)*SD_2L1^2)/(sum(n_2L1) - n())) %>% 
    summarize(mean_2L1 = sum(mean_2L1),
              mean_L1 = sum(mean_L1),
              SD_2L1 = sqrt(sum(SD_2L1)),
              n_2L1 = sum(n_2L1), # compute new sample size for 2L1
              # create collapsed string value for bilingual_group:
              bilingual_group = paste(sort(unique(bilingual_group)), collapse = "_")) %>%   
    # re-compute effect sizes, their variances, se's and weights:
    mutate(mean_difference = mean_2L1 - mean_L1,
           d = ifelse(SD_2L1 == 0 && SD_L1 == 0, 0, abs(((mean_2L1 - mean_L1)/(sqrt((((n_2L1 - 1) * SD_2L1^2) + ((n_L1 - 1) * SD_L1^2)) / (n_2L1 + n_L1 - 2)))))),
           g = d*(1 - (3/(4*(n_2L1 + n_L1 - 2) - 1))),
           g_var = (((n_2L1 + n_L1)/(n_2L1*n_L1)) + (d^2/(2*(n_2L1 + n_L1))))*(1 - (3/(4*(n_2L1 + n_L1 - 2) - 1))),
           g_SE = sqrt(g_var),
           g_W = 1/g_var,
           # change potential predictors to factors:
           target_language = as.factor(target_language),
           task_type = as.factor(task_type), 
           task_detailed = as.factor(task_detailed), 
           linguistic_property = as.factor(linguistic_property), 
           surface_overlap_author = as.factor(surface_overlap_author), 
           target_or_child_system = as.factor(target_or_child_system))
  
  # create g_correct_sign:
  dat1$g_correct_sign <- 0   # placeholder 
  for(i in 1:nrow(dat1)){
    if( (dat1[i,]$mean_difference > 0 && dat1[i,]$predicted_direction_difference_2L1 == "higher") || (dat1[i,]$mean_difference < 0 && dat1[i,]$predicted_direction_difference_2L1 == "lower") || dat1[i,]$predicted_direction_difference_2L1 == "higher_or_lower" ){
      dat1[i,]$g_correct_sign <- dat1[i,]$g
    } else if( (dat1[i,]$mean_difference < 0 && dat1[i,]$predicted_direction_difference_2L1 == "higher") || (dat1[i,]$mean_difference > 0 && dat1[i,]$predicted_direction_difference_2L1 == "lower") || dat1[i,]$predicted_direction_difference_2L1 == "equal" ){
      dat1[i,]$g_correct_sign <- -1*dat1[i,]$g
    }
  }
  
  # only include test cases of CLI
  dat1 <- dat1 %>% filter(CLI_predicted == "yes", target_language=="english")
  
  # zonder predictor(s)
  model1 <- rma.mv(g_correct_sign, g_var, data = dat1, random = list(~ 1|data_collection/task_number, ~1|bilingual_group, ~1|linguistic_property))
  
  # Extract the effect-size ($yi) and the sampling variance ($vi) as well as the include/skip list ($not.na) and the row name (dat1$short_cite)
  oData <- data.frame(
    effectSize = model1$yi,
    sampling = model1$vi
  )  
  oBack <- jsonlite::toJSON(oData)
  #  oBack <- jsonlite::toJSON(model1)
  
  # Return what we found
  return ( oBack )
}

multilingEntry <- function(dataset, calling="") {
    logdebug("Start multilingEntry '%s'", calling, logger = 'runtime')

    # This is the main entry point
    if (calling == "" | calling == "forestprepare") {
        # Call forest prepare
        oBack <- forestPrepare(dataset)

        return( oBack )
    } else if (calling == "debug" | calling == "test") {
        list(bericht = calling, status = "alles goed")
    } else {
        list(bericht = calling, status = "Dit commando is onbekend")
    }
}